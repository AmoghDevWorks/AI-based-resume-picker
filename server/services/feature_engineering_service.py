from services.skill_service import (
    SkillService
)

from services.career_service import (
    CareerService
)

from services.activity_service import (
    ActivityService
)

from services.consistency_service import (
    ConsistencyService
)

from services.honeypot_service import (
    HoneypotService
)


class FeatureEngineeringService:

    def __init__(
        self
    ):

        self.skill_service = (
            SkillService()
        )

        self.career_service = (
            CareerService()
        )

        self.activity_service = (
            ActivityService()
        )

        self.consistency_service = (
            ConsistencyService()
        )

        self.honeypot_service = (
            HoneypotService()
        )

    def build_features(
        self,
        candidate,
        jd_skills,
        semantic_similarity
    ):

        return {

            "semantic_similarity":
                semantic_similarity,

            "skill_overlap":
                self.skill_service.compute(
                    candidate,
                    jd_skills
                ),

            "career_stability":
                self.career_service.compute(
                    candidate
                ),

            "activity_score":
                self.activity_service.compute(
                    candidate
                ),

            "consistency_score":
                self.consistency_service.compute(
                    candidate
                ),

            "honeypot_penalty":
                self.honeypot_service.compute(
                    candidate
                )

        }