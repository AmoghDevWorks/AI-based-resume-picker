"""
controller/rank.py
==================
Facade for the whole /rank request.

Pipeline
--------
  1. Extract JD text (pdf/docx) + candidate records (jsonl)
  2. Score & rank ALL candidates in memory (utils/scoring.py):
       - Honeypot filtering BEFORE TF-IDF (inside engine.run)
       - TF-IDF + skill match + experience + platform signals
       - Notice-period bonus
       - Min-score filter
  3. Slice top-100 from the cleaned, ranked pool
  4. Embed the JD + top-100 candidates
  5. Persist those embeddings to the session vector store  ← LAST step
  6. Return full above-threshold results (all, not just top-100) so the
     caller can inspect the complete ranked & cleaned pool.

NOTE: HoneypotFilter is called once, inside CandidateRankingEngine.run(),
      before the TF-IDF matrix is built.  rank.py reads the counts from
      RankingResult — it does NOT run a second honeypot pass.

MEMORY NOTE: CandidateRankingEngine.run() deletes its `raw_candidates`
      parameter internally as soon as it has extracted everything it
      needs from it (see scoring.py). For that deletion to actually
      free memory, this module must not hold its own live reference to
      raw_candidates afterward. `total_candidates_received` is therefore
      captured via len() BEFORE engine.run() is called, and used in
      place of len(raw_candidates) everywhere below. Do not reintroduce
      a post-engine.run() reference to raw_candidates.
"""

import json

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from .utils.pdfWordFileExtractor import extract_text, extract_jsonl_records
from .utils.scoring import CandidateRankingEngine, JobDescription, ScoringConfig
from .utils.embedding import get_embedding, get_embeddings
from .utils.vectorDB import VectorDB

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
    print("A")
    jd_text = await extract_text(jd)

    print("B")
    jd_description = JobDescription.from_text(jd_text)

    print("C")
    raw_candidates, decode_skipped = await extract_jsonl_records(candidates)

    # ── Capture this NOW, before engine.run(). engine.run() deletes its
    # raw_candidates parameter as soon as it's done extracting what it
    # needs from it (the single biggest memory release in the whole
    # pipeline, typically 2-4 GB at 100k candidates). If this module
    # keeps its own reference to raw_candidates alive past this point,
    # that deletion is a no-op and the memory never actually frees.
    total_candidates_received = len(raw_candidates)

    # ── 2. Score & rank — CPU-bound; run off the event loop ──────────
    # engine.run() internally:
    #   a) scores all candidates (skill, experience, platform)
    #   b) runs HoneypotFilter BEFORE building the TF-IDF matrix
    #   c) runs TF-IDF only on clean candidates
    #   d) aggregates + applies notice bonus + filters by min_final_score
    # The honeypot counts are surfaced via RankingResult fields.
    print("D", total_candidates_received)

    engine = CandidateRankingEngine(ScoringConfig())

    print("E")

    result = await run_in_threadpool(
        engine.run,
        jd_description,
        raw_candidates
    )

    # raw_candidates has been deleted inside engine.run() by this point.
    # Do NOT reference it below — use total_candidates_received instead.

    print("F")

    if result.dataframe.empty:
        return {
            "jd_filename": jd.filename,
            "candidates_filename": candidates.filename,
            "top_k": top_k,
            "total_candidates_received": total_candidates_received,
            "candidates_skipped": decode_skipped + result.skipped_records,
            "candidates_above_threshold": 0,
            "honeypots_removed": result.honeypots_removed,
            "honeypot_ids": result.honeypot_ids,
            "candidates_returned": 0,
            "top_100": [],
            "all_above_threshold": [],
            "message": "No usable candidate records, or none cleared the score threshold.",
        }

    # result.dataframe already contains ONLY clean candidates above
    # min_final_score, sorted descending by final_score.
    above_threshold_df = result.dataframe
    candidates_by_id   = result.candidates_by_id

    print(
        f"[rank] {len(above_threshold_df)} candidate(s) in pool after scoring & "
        f"honeypot filtering. ({result.honeypots_removed} honeypot(s) removed)"
    )

    # ── 3. Slice top-100 ─────────────────────────────────────────────
    final_top_k = min(top_k, TOP_K_FINAL)
    top_df = above_threshold_df.head(final_top_k)

    filtered_candidates = [
        candidates_by_id[cid]
        for cid in top_df["candidate_id"]
        if cid in candidates_by_id
    ]

    # ── 4. Embed the JD + top-100 candidates ────────────────────────
    candidate_texts      = [c.to_resume_text() for c in filtered_candidates]
    jd_embedding         = await run_in_threadpool(get_embedding, jd_text)
    candidate_embeddings = await run_in_threadpool(get_embeddings, candidate_texts)

    # ── 5. Persist to the vector store ──────────────────────────────
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

    # ── 6. Serialise results — numpy/pandas types → plain JSON ───────
    top_100_records = json.loads(
        top_df.reset_index().to_json(orient="records")
    )
    all_above_threshold_records = json.loads(
        above_threshold_df.reset_index().to_json(orient="records")
    )

    print(f"[rank] Returning top {len(top_100_records)} candidates.")

    return {
        "jd_filename": jd.filename,
        "candidates_filename": candidates.filename,
        "top_k": final_top_k,
        "total_candidates_received": total_candidates_received,
        "candidates_skipped": decode_skipped + result.skipped_records,
        "candidates_above_threshold": len(above_threshold_df),
        "honeypots_removed": result.honeypots_removed,
        "honeypot_ids": result.honeypot_ids,
        "candidates_returned": len(top_100_records),
        # The competition submission: exactly top-100 (or fewer if pool is small)
        "top_100": top_100_records,
        # Full cleaned pool above threshold — useful for debugging / inspection
        "all_above_threshold": all_above_threshold_records,
    }