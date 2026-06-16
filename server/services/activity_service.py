class ActivityService:

    def compute(
        self,
        candidate
    ) -> float:

        signals = candidate[
            "redrob_signals"
        ]

        score = (

            0.30
            *
            signals[
                "recruiter_response_rate"
            ]

            +

            0.30
            *
            signals[
                "interview_completion_rate"
            ]

            +

            0.20
            *
            min(
                signals[
                    "profile_views_received_30d"
                ]
                /
                100,
                1
            )

            +

            0.20
            *
            min(
                signals[
                    "saved_by_recruiters_30d"
                ]
                /
                20,
                1
            )

        )

        return score