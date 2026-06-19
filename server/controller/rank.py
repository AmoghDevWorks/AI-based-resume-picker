"""
controller/rank.py
==================
Facade for the whole /rank request.

Pipeline
--------
  1. Extract JD text (pdf/docx) + candidate records (jsonl)
  2. Score & rank ALL candidates in memory (utils/scoring.py):
       TF-IDF + skill match + experience + platform signals,
       then the notice-period bonus.
  3. Filter by min_final_score  →  "above-threshold" pool
  4. Pass that pool through HoneypotFilter:
       – detects impossible timelines, skill inflation, overlaps, etc.
       – applies per-signal score penalties
       – hard-discards profiles whose cumulative penalty ≥ threshold
  5. Slice top-100 from the cleaned pool
  6. Embed the JD + top-100 candidates
  7. Persist those embeddings to the session vector store  ← LAST step
  8. Return full above-threshold results (all, not just top-100) so the
     caller can inspect the complete ranked & cleaned pool.
"""

import json

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from .utils.pdfWordFileExtractor import extract_text, extract_jsonl_records
from .utils.scoring import CandidateRankingEngine, JobDescription, ScoringConfig
from .utils.embedding import get_embedding, get_embeddings
from .utils.vectorDB import VectorDB
from .utils.honeypotPenalty import HoneypotFilter, HoneypotConfig

# One VectorDB per session, created once and reused across requests.
# NOTE: session_id is hardcoded for now — swap in real per-user id once
# auth is wired up.
db = VectorDB(embedding_dim=384, session_id="user_123")

# Top-N to embed & persist (competition requires exactly 100).
TOP_K_FINAL = 100


async def rank_candidates(
    jd: UploadFile,
    candidates: UploadFile,
    top_k: int,
):
    # ── 1. Extract ───────────────────────────────────────────────────
    jd_text = await extract_text(jd)
    jd_description = JobDescription.from_text(jd_text)
    raw_candidates, decode_skipped = await extract_jsonl_records(candidates)

    # ── 2. Score & rank — CPU-bound; run off the event loop ──────────
    engine = CandidateRankingEngine(ScoringConfig())
    result = await run_in_threadpool(engine.run, jd_description, raw_candidates)

    if result.dataframe.empty:
        return {
            "jd_filename": jd.filename,
            "candidates_filename": candidates.filename,
            "top_k": top_k,
            "total_candidates_received": len(raw_candidates),
            "candidates_skipped": decode_skipped + result.skipped_records,
            "candidates_above_threshold": 0,
            "honeypots_removed": 0,
            "candidates_returned": 0,
            "top_100": [],
            "all_above_threshold": [],
            "message": "No usable candidate records, or none cleared the score threshold.",
        }

    # result.dataframe already contains ONLY candidates above min_final_score,
    # sorted descending by final_score.
    above_threshold_df = result.dataframe          # full above-threshold pool
    candidates_by_id   = result.candidates_by_id

    print(
        f"[rank] {len(above_threshold_df)} candidate(s) cleared the score threshold "
        f"before honeypot filtering."
    )

    # ── 3 & 4. Honeypot detection & penalty ─────────────────────────
    honeypot_filter = HoneypotFilter(HoneypotConfig())
    cleaned_df, removed_ids = await run_in_threadpool(
        honeypot_filter.apply,
        above_threshold_df,
        candidates_by_id,
    )

    print(
        f"[rank] {len(cleaned_df)} candidate(s) remain after honeypot filtering "
        f"({len(removed_ids)} discarded)."
    )

    # ── 5. Slice top-100 ─────────────────────────────────────────────
    final_top_k = min(top_k, TOP_K_FINAL)
    top_df = cleaned_df.head(final_top_k)

    filtered_candidates = [
        candidates_by_id[cid]
        for cid in top_df["candidate_id"]
        if cid in candidates_by_id
    ]

    # ── 6. Embed the JD + top-100 candidates ────────────────────────
    candidate_texts   = [c.to_resume_text() for c in filtered_candidates]
    jd_embedding      = await run_in_threadpool(get_embedding, jd_text)
    candidate_embeddings = await run_in_threadpool(get_embeddings, candidate_texts)

    # ── 7. Persist to the vector store ──────────────────────────────
    db.insert(
        [jd_embedding],
        metadata=[{"id": "jd", "type": "job_description", "filename": jd.filename}],
    )
    db.insert(
        candidate_embeddings,
        metadata=[
            {
                "id": c.candidate_id,
                "type": "candidate",
                "name": c.profile.get("anonymized_name", ""),
            }
            for c in filtered_candidates
        ],
    )
    db.save()

    # ── 8. Serialise results — numpy/pandas types → plain JSON ───────
    top_100_records = json.loads(
        top_df.reset_index().to_json(orient="records")
    )
    all_above_threshold_records = json.loads(
        cleaned_df.reset_index().to_json(orient="records")
    )

    print(f"[rank] Returning top {len(top_100_records)} candidates.")

    return {
        "jd_filename": jd.filename,
        "candidates_filename": candidates.filename,
        "top_k": final_top_k,
        "total_candidates_received": len(raw_candidates),
        "candidates_skipped": decode_skipped + result.skipped_records,
        "candidates_above_threshold": len(above_threshold_df),
        "honeypots_removed": len(removed_ids),
        "honeypot_ids": removed_ids,
        "candidates_returned": len(top_100_records),
        # The competition submission: exactly top-100 (or fewer if pool is small)
        "top_100": top_100_records,
        # Full cleaned pool above threshold — useful for debugging / inspection
        "all_above_threshold": all_above_threshold_records,
    }