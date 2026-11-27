from src.ingestion.run import run as run_ingestion
from src.transformation.transform import run_transformations


def run_pipeline(limit=5):
    print("Starting ingestion...")
    run_ingestion(limit=limit)

    print("\nStarting transformations...")
    run_transformations()

    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    run_pipeline()
