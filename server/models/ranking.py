from pydantic import BaseModel

from typing import List


class RankedCandidate(BaseModel):

    candidate_id: str

    score: float

    reasoning: str


class RankingResponse(BaseModel):

    top_k: int

    num_results: int

    results: List[RankedCandidate]