import faiss
import numpy as np
import pickle
import os


class VectorDB:
    def __init__(self, embedding_dim: int):
        self.embedding_dim = embedding_dim
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.metadata = []

    def insert(self, embeddings, ids=None):
        """
        embeddings: list or numpy array of shape (n, embedding_dim)
        ids: optional list of ids corresponding to embeddings
        """
        embeddings = np.array(embeddings, dtype=np.float32)

        self.index.add(embeddings)

        if ids is None:
            ids = list(range(len(self.metadata), len(self.metadata) + len(embeddings)))

        self.metadata.extend(ids)

    def search(self, query_embedding, k=5):
        """
        Returns top-k closest vectors.
        """
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

    def save(self, folder_path="vectorDB"):
        """
        Saves FAISS index and metadata.
        """
        os.makedirs(folder_path, exist_ok=True)

        faiss.write_index(self.index, os.path.join(folder_path, "faiss_index.bin"))

        with open(os.path.join(folder_path, "metadata.pkl"), "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self, folder_path="vectorDB"):
        """
        Loads FAISS index and metadata.
        """
        self.index = faiss.read_index(
            os.path.join(folder_path, "faiss_index.bin")
        )

        with open(os.path.join(folder_path, "metadata.pkl"), "rb") as f:
            self.metadata = pickle.load(f)