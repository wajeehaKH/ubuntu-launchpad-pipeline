
from src.ingestion.launchpad_client import get_launchpad, fetch_new_tasks
from src.ingestion.bugs import fetch_bug_and_task
from src.ingestion.repository import save_bug_and_task


def run(limit=5):
    lp = get_launchpad()
    tasks = fetch_new_tasks(limit=limit)

    for task in tasks:
        records = fetch_bug_and_task(lp, task)

        save_bug_and_task(
            records["bug"],
            records["task"],
        )

        print(
            f"Ingested bug {records['bug']['id']}: "
            f"{records['bug']['title']}"
        )

    print(f"\nSuccessfully ingested {len(tasks)} tasks.")


if __name__ == "__main__":
    run()
