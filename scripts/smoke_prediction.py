import pandas as pd
from managers.prediction_manager import PredictionManager


def main():
    pm = PredictionManager()
    df = pd.DataFrame(
        {
            "gene": ["FAKE_GENE_A", "FAKE_GENE_B"],
            "expression": [1.2, 3.4],
        }
    )
    result = pm.run_prediction(df, sample_name="smoke_sample", user_notes="smoke test")
    print(
        {
            "prediction_id": result["prediction_id"],
            "final_prediction": result["final_prediction"],
            "is_tumor": result["is_tumor"],
        }
    )


if __name__ == "__main__":
    main()
