from collections import defaultdict


class SkillService:

    def compute(
        self,
        candidate,
        jd_skills
    ) -> float:

        candidate_skills = {

            skill["name"].lower()

            for skill
            in candidate["skills"]

        }

        jd_skills = {

            skill.lower()

            for skill
            in jd_skills

        }

        overlap = len(
            candidate_skills &
            jd_skills
        )

        denominator = max(
            1,
            len(
                jd_skills
            )
        )

        return overlap / denominator