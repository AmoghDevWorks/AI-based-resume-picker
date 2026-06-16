import pandas as pd
from pathlib import Path


class FeatureRepository:

    def __init__(
        self
    ):

        self.feature_path = (
            Path(
                "artifacts"
            )
            /
            "feature_table.parquet"
        )

    def save_features(
        self,
        feature_table: pd.DataFrame
    ):

        feature_table.to_parquet(
            self.feature_path,
            index=False
        )

    def load_features(
        self
    ) -> pd.DataFrame:

        if (
            not self.feature_path.exists()
        ):

            return pd.DataFrame()

        return pd.read_parquet(
            self.feature_path
        )