from pydantic import BaseModel

from typing import List, Optional


class Skill(BaseModel):

    name: str

    proficiency: str

    endorsements: int

    duration_months: Optional[int] = None


class Profile(BaseModel):

    headline: str

    summary: str

    current_title: str

    current_company: str

    years_of_experience: float


class Candidate(BaseModel):

    candidate_id: str

    profile: Profile

    skills: List[Skill]