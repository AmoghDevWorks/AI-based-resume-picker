import json


class CandidateRepository:

    def load_candidates(
        self,
        candidates_path: str
    ) -> list:

        candidates = []

        with open(
            candidates_path,
            "r",
            encoding="utf-8"
        ) as f:

            for line in f:

                candidates.append(
                    json.loads(
                        line
                    )
                )

        return candidates

    def get_candidate_by_id(
        self,
        candidate_id: str,
        candidates: list
    ) -> dict | None:

        for candidate in candidates:

            if (
                candidate[
                    "candidate_id"
                ]
                == candidate_id
            ):

                return candidate

        return None