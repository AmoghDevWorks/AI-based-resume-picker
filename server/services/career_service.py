class CareerService:

    def compute(
        self,
        candidate
    ) -> float:

        history = candidate[
            "career_history"
        ]

        if len(
            history
        ) == 0:

            return 0.0

        total_duration = sum(

            job[
                "duration_months"
            ]

            for job
            in history

        )

        average_duration = (

            total_duration
            /
            len(
                history
            )

        )

        score = min(
            average_duration / 24,
            1.0
        )

        return score