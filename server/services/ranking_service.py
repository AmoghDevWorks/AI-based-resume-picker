from services.document_service import (
    DocumentService
)

from services.retrieval_service import (
    RetrievalService
)

from services.feature_engineering_service import (
    FeatureEngineeringService
)

from services.scoring_service import (
    ScoringService
)

from services.reasoning_service import (
    ReasoningService
)


class RankingService:

    def __init__(
        self
    ):

        self.document_service = (
            DocumentService()
        )

        self.retrieval_service = (
            RetrievalService()
        )

        self.feature_service = (
            FeatureEngineeringService()
        )

        self.scoring_service = (
            ScoringService()
        )

        self.reasoning_service = (
            ReasoningService()
        )

    def rank(
        self,
        jd_path,
        candidates_path,
        top_k=100
    ):

        jd_text = (

            self.document_service
            .extract_text(
                jd_path
            )

        )

        retrieved_candidates = (

            self.retrieval_service
            .retrieve(
                jd_text,
                candidates_path
            )

        )

        jd_skills = []

        ranked_candidates = []

        for candidate in retrieved_candidates:

            semantic_similarity = 1.0

            features = (

                self.feature_service
                .build_features(

                    candidate,

                    jd_skills,

                    semantic_similarity

                )

            )

            score = (

                self.scoring_service
                .compute_score(
                    features
                )

            )

            reasoning = (

                self.reasoning_service
                .generate(
                    candidate,
                    score
                )

            )

            ranked_candidates.append(

                {

                    "candidate_id":
                        candidate[
                            "candidate_id"
                        ],

                    "score":
                        score,

                    "reasoning":
                        reasoning

                }

            )

        ranked_candidates.sort(

            key=lambda x:
            x[
                "score"
            ],

            reverse=True

        )

        return ranked_candidates[
            :top_k
        ]