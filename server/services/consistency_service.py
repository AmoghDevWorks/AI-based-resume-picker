class ConsistencyService:

    def compute(
        self,
        candidate
    ) -> float:

        score = 1.0

        history = candidate[
            "career_history"
        ]

        skills = candidate[
            "skills"
        ]

        for skill in skills:

            if (

                skill[
                    "proficiency"
                ]
                ==
                "expert"

                and

                skill.get(
                    "duration_months",
                    0
                )

                <
                6

            ):

                score -= 0.1

        for job in history:

            if (

                job[
                    "duration_months"
                ]

                <= 0

            ):

                score -= 0.1

        return max(
            score,
            0.0
        )