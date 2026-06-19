# controller/rank.py
"""
Facade for the whole /rank request.

Pipeline:
  1. Extract JD text (pdf/docx) + candidate records (jsonl)
  2. Score & rank candidates in memory (utils/scoring.py — same logic
     as the resume matcher: TF-IDF + skill match + experience + platform
     signals, then the notice-period bonus, then the final_score > 40 filter)
  3. Embed the JD and the candidates that cleared the bar
  4. Persist those embeddings to the session's vector store — LAST step
  5. Return the filtered, ranked results
"""

import json

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from .utils.pdfWordFileExtractor import extract_text, extract_jsonl_records
from .utils.scoring import CandidateRankingEngine, JobDescription, ScoringConfig
from .utils.embedding import get_embedding, get_embeddings
from .utils.vectorDB import VectorDB

# One VectorDB per session, created once and reused across requests.
# NOTE: session_id is hardcoded for now (same as the original file), so
# every request currently shares one store — swap in a real per-user/
# request session id once auth is wired up.
db = VectorDB(embedding_dim=384, session_id="user_123")


async def rank_candidates(
    jd: UploadFile,
    candidates: UploadFile,
    top_k: int,
):
    # ── 1. Extract ───────────────────────────────────────────────────
    jd_text = await extract_text(jd)
    jd_description = JobDescription.from_text(jd_text)

    raw_candidates, decode_skipped = await extract_jsonl_records(candidates)

    # ── 2. Score & rank — CPU-bound (TF-IDF + sklearn), run off the
    #       event loop so a big upload doesn't stall other requests ──
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
            "candidates_returned": 0,
            "results": [],
            "message": "No usable candidate records, or none cleared the score threshold.",
        }

    final_df = result.dataframe.head(top_k)
    filtered_candidates = [
        result.candidates_by_id[cid] for cid in final_df["candidate_id"]
    ]

    # ── 3. Embed the JD + the filtered candidates ──────────────────────
    candidate_texts = [c.to_resume_text() for c in filtered_candidates]
    jd_embedding = await run_in_threadpool(get_embedding, jd_text)
    candidate_embeddings = await run_in_threadpool(get_embeddings, candidate_texts)

    # ── 4. Persist to the vector store (the actual "last step") ───────
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

    # ── 5. Return filtered, ranked results ─────────────────────────────
    # final_df can hold numpy scalar types (from pandas) — round-trip
    # through pandas' own JSON encoder so the response is plain-JSON-safe.
    results = json.loads(final_df.reset_index().to_json(orient="records"))

    return {
        "jd_filename": jd.filename,
        "candidates_filename": candidates.filename,
        "top_k": top_k,
        "total_candidates_received": len(raw_candidates),
        "candidates_skipped": decode_skipped + result.skipped_records,
        "candidates_above_threshold": len(result.dataframe),
        "candidates_returned": len(final_df),
        "results": results,
    }