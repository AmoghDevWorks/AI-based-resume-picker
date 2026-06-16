import pickle
from pathlib import Path


class EmbeddingRepository:

    def __init__(
        self
    ):

        self.embedding_path = (
            Path(
                "artifacts"
            )
            /
            "candidate_embeddings.pkl"
        )

    def save_embeddings(
        self,
        embeddings: dict
    ):

        with open(
            self.embedding_path,
            "wb"
        ) as f:

            pickle.dump(
                embeddings,
                f
            )

    def load_embeddings(
        self
    ) -> dict:

        if (
            not self.embedding_path.exists()
        ):

            return {}

        with open(
            self.embedding_path,
            "rb"
        ) as f:

            return pickle.load(
                f
            )