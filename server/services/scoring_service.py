class ScoringService:

    def compute_score(
        self,
        features
    ):

        score = (

            0.35
            *
            features[
                "semantic_similarity"
            ]

            +

            0.20
            *
            features[
                "skill_overlap"
            ]

            +

            0.15
            *
            features[
                "career_stability"
            ]

            +

            0.15
            *
            features[
                "activity_score"
            ]

            +

            0.15
            *
            features[
                "consistency_score"
            ]

        )

        score -= (

            features[
                "honeypot_penalty"
            ]

        )

        return score