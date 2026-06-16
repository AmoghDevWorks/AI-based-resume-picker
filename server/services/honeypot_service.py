class HoneypotService:

    def compute(
        self,
        candidate
    ) -> float:

        penalty = 0.0

        skills = candidate[
            "skills"
        ]

        history = candidate[
            "career_history"
        ]

        #
        # Expert skill with
        # unrealistic duration
        #

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
                3

            ):

                penalty += 0.10

        #
        # Impossible jobs
        #

        for job in history:

            if (

                job[
                    "duration_months"
                ]

                <= 0

            ):

                penalty += 0.10

        return min(
            penalty,
            1.0
        )