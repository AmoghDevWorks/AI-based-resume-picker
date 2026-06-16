from repositories.candidate_repository import (
    CandidateRepository
)

from services.embedding_service import (
    EmbeddingService
)

from services.vector_service import (
    VectorService
)

from services.bm25_service import (
    BM25Service
)


class RetrievalService:

    def __init__(
        self
    ):

        self.embedding_service = (
            EmbeddingService()
        )

        self.vector_service = (
            VectorService()
        )

        self.bm25_service = (
            BM25Service()
        )

        self.candidate_repository = (
            CandidateRepository()
        )

    def build_candidate_text(
        self,
        candidate
    ):

        profile = candidate[
            "profile"
        ]

        skills = " ".join(

            skill["name"]

            for skill
            in candidate["skills"]

        )

        return f"""

        {profile['current_title']}

        {profile['summary']}

        Skills:

        {skills}

        """

    def retrieve(
        self,
        jd_text: str,
        candidates_path: str,
        top_k=500
    ):

        candidates = (
            self.candidate_repository
            .load_candidates(
                candidates_path
            )
        )

        candidate_texts = [

            self.build_candidate_text(
                candidate
            )

            for candidate
            in candidates

        ]

        candidate_embeddings = (
            self.embedding_service
            .encode_batch(
                candidate_texts
            )
        )

        jd_embedding = (
            self.embedding_service
            .encode(
                jd_text
            )
        )

        index = (
            self.vector_service
            .build_index(
                candidate_embeddings
            )
        )

        _, vector_indices = (
            self.vector_service
            .search(
                index,
                jd_embedding,
                top_k
            )
        )

        bm25 = (
            self.bm25_service
            .build(
                candidate_texts
            )
        )

        bm25_indices = (
            self.bm25_service
            .search(
                bm25,
                jd_text,
                top_k
            )
        )

        hybrid_indices = list(

            set(
                vector_indices
            )

            |
            set(
                bm25_indices
            )

        )

        return [

            candidates[idx]

            for idx
            in hybrid_indices

        ]