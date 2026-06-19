import faiss
import numpy as np
import pickle
import os
import shutil


class VectorDB:
    def __init__(self, embedding_dim: int, session_id: str):
        self.embedding_dim = embedding_dim
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.metadata = []

        # Create vectorDB/session_id folder
        self.folder_path = os.path.join("vectorDB", session_id)
        os.makedirs(self.folder_path, exist_ok=True)

    def insert(self, embeddings, ids=None):
        embeddings = np.array(embeddings, dtype=np.float32)

        self.index.add(embeddings)

        if ids is None:
            ids = list(
                range(
                    len(self.metadata),
                    len(self.metadata) + len(embeddings)
                )
            )

        self.metadata.extend(ids)

    def search(self, query_embedding, k=5):
        query_embedding = np.array([query_embedding], dtype=np.float32)

        distances, indices = self.index.search(query_embedding, k)

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1:
                results.append({
                    "id": self.metadata[idx],
                    "distance": float(dist)
                })

        return results

    def save(self):
        faiss.write_index(
            self.index,
            os.path.join(self.folder_path, "faiss_index.bin")
        )

        with open(
            os.path.join(self.folder_path, "metadata.pkl"),
            "wb"
        ) as f:
            pickle.dump(self.metadata, f)

    def load(self):
        self.index = faiss.read_index(
            os.path.join(self.folder_path, "faiss_index.bin")
        )

        with open(
            os.path.join(self.folder_path, "metadata.pkl"),
            "rb"
        ) as f:
            self.metadata = pickle.load(f)

    def delete(self):
        """
        Delete the entire vectorDB/session_id folder.
        """
        if os.path.exists(self.folder_path):
            shutil.rmtree(self.folder_path)