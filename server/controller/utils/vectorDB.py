# controller/utils/vectorDB.py
"""
FAISS-backed vector store for one ranking session. Stores the JD and the
filtered candidates' embeddings together, with metadata, so they can be
told apart and searched later.
"""

import os
import pickle
import shutil
from typing import List

# pyrefly: ignore [missing-import]
import faiss
import numpy as np


class VectorDB:
    """
    One VectorDB instance == one session's worth of embeddings, persisted
    to disk under vectorDB/<session_id>/.

    Each vector is stored alongside a metadata dict (not just a bare id),
    e.g. {"id": "jd", "type": "job_description", "filename": "jd.pdf"} or
    {"id": "cand_42", "type": "candidate", "name": "..."} — so a search
    result tells you what it matched, not just which row number.
    """

    def __init__(self, embedding_dim: int, session_id: str):
        self.embedding_dim = embedding_dim
        self.session_id = session_id
        # Embeddings from SentenceTransformer are L2-normalized, so inner
        # product == cosine similarity. IndexFlatIP gives directly
        # interpretable similarity scores (higher = closer).
        self.index = faiss.IndexFlatIP(embedding_dim)
        self.metadata: List[dict] = []

        self.folder_path = os.path.join("vectorDB", session_id)
        os.makedirs(self.folder_path, exist_ok=True)

    def insert(self, embeddings: List[List[float]], metadata: List[dict]):
        """
        Add a batch of embeddings. `metadata` must be the same length as
        `embeddings` — one dict per vector.
        """
        if len(embeddings) != len(metadata):
            raise ValueError(
                f"embeddings ({len(embeddings)}) and metadata ({len(metadata)}) length mismatch"
            )
        if not embeddings:
            return

        vectors = np.array(embeddings, dtype=np.float32)
        self.index.add(vectors)
        self.metadata.extend(metadata)

    def search(self, query_embedding: List[float], k: int = 5) -> List[dict]:
        if self.index.ntotal == 0:
            return []

        query = np.array([query_embedding], dtype=np.float32)
        scores, indices = self.index.search(query, min(k, self.index.ntotal))

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx != -1:
                results.append({
                    **self.metadata[idx],
                    "similarity": float(score),  # higher = more similar
                })
        return results

    def save(self):
        faiss.write_index(
            self.index,
            os.path.join(self.folder_path, "faiss_index.bin"),
        )
        with open(os.path.join(self.folder_path, "metadata.pkl"), "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self) -> bool:
        """
        Load a previously saved index for this session, if one exists.
        Returns True if something was loaded, False if there's nothing yet.
        """
        index_path = os.path.join(self.folder_path, "faiss_index.bin")
        meta_path = os.path.join(self.folder_path, "metadata.pkl")

        if not (os.path.exists(index_path) and os.path.exists(meta_path)):
            return False

        self.index = faiss.read_index(index_path)
        with open(meta_path, "rb") as f:
            self.metadata = pickle.load(f)
        return True

    def delete(self):
        """
        Delete the entire vectorDB/session_id folder.

        Call this explicitly when a session is actually finished — NOT
        immediately after save(), or you'd be wiping the embeddings the
        same request just stored.
        """
        if os.path.exists(self.folder_path):
            shutil.rmtree(self.folder_path)