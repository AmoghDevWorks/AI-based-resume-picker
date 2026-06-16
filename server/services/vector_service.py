import numpy as np
import faiss


class VectorService:

    def build_index(
        self,
        embeddings
    ):

        embeddings = np.array(
            embeddings,
            dtype="float32"
        )

        dimension = (
            embeddings.shape[1]
        )

        index = (
            faiss.IndexFlatIP(
                dimension
            )
        )

        index.add(
            embeddings
        )

        return index

    def search(
        self,
        index,
        query_embedding,
        top_k=500
    ):

        query_embedding = (
            np.array(
                [query_embedding],
                dtype="float32"
            )
        )

        scores, indices = (
            index.search(
                query_embedding,
                top_k
            )
        )

        return (
            scores[0],
            indices[0]
        )