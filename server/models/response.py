# models/response.py

from typing import List

from pydantic import BaseModel


class RankedCandidateResponse(
    BaseModel
):

    candidate_id: str

    score: float

    reasoning: str


class RankingResponse(
    BaseModel
):

    top_k: int

    num_results: int

    results: List[
        RankedCandidateResponse
    ]
