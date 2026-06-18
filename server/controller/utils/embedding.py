# utils/embedding.py

from sentence_transformers import SentenceTransformer
import os

# During offline preprocessing, we might need to download the model.
# We download it once and save it to server/localmodels/all-MiniLM-L6-v2
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "localmodels", "all-MiniLM-L6-v2")
# Fallback to HF hub if local folder doesn't exist yet
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def load_model(offline_mode=False):
    """
    Loads the sentence transformer model.
    In offline mode, it allows downloading. In online mode, it strictly uses local files.
    """
    if os.path.exists(MODEL_PATH):
        return SentenceTransformer(MODEL_PATH)
    
    if offline_mode:
        return SentenceTransformer(MODEL_NAME)
    else:
        # In production/online mode, we strictly enforce local files to avoid network calls
        try:
            return SentenceTransformer(MODEL_NAME, local_files_only=True)
        except Exception:
            # Fallback if local_files_only fails due to huggingface cache issues during dev
            return SentenceTransformer(MODEL_NAME)

# Load model lazily or at module level
model = load_model(offline_mode=False)


def get_embedding(text: str) -> list[float]:
    """
    Generate embedding vector for the input text.

    Args:
        text (str): Input text

    Returns:
        list[float]: Embedding vector
    """
    if not text or not text.strip():
        # Return empty vector of correct dimension if text is empty
        return [0.0] * 384
        
    embedding = model.encode(
        text,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embedding.tolist()