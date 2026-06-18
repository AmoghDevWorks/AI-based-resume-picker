# utils/embeddings.py

from sentence_transformers import SentenceTransformer

# Load model once when the module is imported
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


def get_embedding(text: str) -> list[float]:
    """
    Generate embedding vector for the input text.

    Args:
        text (str): Input text

    Returns:
        list[float]: Embedding vector
    """
    embedding = model.encode(
        text,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embedding.tolist()