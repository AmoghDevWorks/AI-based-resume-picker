# controller/utils/embedding.py
"""
Wraps the SentenceTransformer model behind a small service class so the
model loads exactly once (it's expensive) and both single-text and
batch embedding go through the same code path.
"""

from typing import List

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Owns the embedding model. One instance is created at import time
    and reused for every request — loading the model per-request would
    be far too slow."""

    _MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self):
        self._model = SentenceTransformer(self._MODEL_NAME)

    def embed(self, text: str) -> List[float]:
        """Embed a single string."""
        vector = self._model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return vector.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed many strings in one batched call — much faster than
        calling embed() in a loop when there are hundreds/thousands of
        candidates to embed."""
        if not texts:
            return []

        vectors = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=64,
            show_progress_bar=False,
        )
        return vectors.tolist()


# Loaded once when this module is first imported, same as the original file.
_service = EmbeddingService()


def get_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for a single piece of text.

    Args:
        text (str): Input text

    Returns:
        list[float]: Embedding vector
    """
    return _service.embed(text)


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embedding vectors for a batch of texts in one call — use this
    for the filtered candidate list instead of calling get_embedding() in
    a loop.

    Args:
        texts (list[str]): Input texts

    Returns:
        list[list[float]]: Embedding vectors, same order as `texts`
    """
    return _service.embed_batch(texts)