class ReasoningService:

    def generate(
        self,
        candidate,
        score
    ):

        title = (
            candidate[
                "profile"
            ][
                "current_title"
            ]
        )

        return (

            f"{title} demonstrates strong "
            f"alignment with the job requirements "
            f"with an overall score of "
            f"{score:.2f}."

        )