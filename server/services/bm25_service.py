from rank_bm25 import BM25Okapi


class BM25Service:

    def build(
        self,
        corpus: list[str]
    ):

        tokenized_corpus = [

            document.lower().split()

            for document
            in corpus

        ]

        return BM25Okapi(
            tokenized_corpus
        )

    def search(
        self,
        bm25,
        query: str,
        top_k=500
    ):

        tokenized_query = (
            query.lower()
            .split()
        )

        scores = (
            bm25.get_scores(
                tokenized_query
            )
        )

        ranked_indices = (
            scores.argsort()[::-1]
        )

        return ranked_indices[
            :top_k
        ]
