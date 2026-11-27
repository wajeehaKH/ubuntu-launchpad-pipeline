import src.ingestion.run as ingestion_run
import pytest

def test_run_handles_empty_task_list(monkeypatch, capsys):
    monkeypatch.setattr(
        ingestion_run,
        "get_launchpad",
        lambda: object(),
    )

    monkeypatch.setattr(
        ingestion_run,
        "fetch_new_tasks",
        lambda limit: [],
    )

    ingestion_run.run()

    captured = capsys.readouterr()

    assert "Successfully ingested 0 tasks." in captured.out


def test_run_processes_and_saves_all_tasks(monkeypatch):
    fake_tasks = [
        {"id": 1},
        {"id": 2},
    ]

    saved_records = []

    monkeypatch.setattr(
        ingestion_run, "get_launchpad", lambda: object()
    )

    monkeypatch.setattr(
        ingestion_run,
        "fetch_new_tasks",
        lambda limit: fake_tasks if limit == 2 else [],
    )

    monkeypatch.setattr(
        ingestion_run,
        "fetch_bug_and_task",
        lambda lp, task: {
            "bug": {"id": task["id"], "title": f"Bug {task['id']}"},
            "task": {"bug_id": task["id"]},
        },
    )

    monkeypatch.setattr(
        ingestion_run,
        "save_bug_and_task",
        lambda bug, task: saved_records.append((bug, task)),
    )

    ingestion_run.run(limit=2)

    assert len(saved_records) == 2
    assert [bug["id"] for bug, task in saved_records] == [1, 2]


def test_run_stops_when_task_processing_fails(monkeypatch):
    fake_tasks = [{"id": 1}, {"id": 2}]
    processed_tasks = []

    monkeypatch.setattr(
        ingestion_run, "get_launchpad", lambda: object()
    )
    monkeypatch.setattr(
        ingestion_run, "fetch_new_tasks", lambda limit: fake_tasks
    )

    def fake_fetch(lp, task):
        processed_tasks.append(task["id"])

        if task["id"] == 1:
            raise RuntimeError("Launchpad request failed")

        return {
            "bug": {"id": task["id"], "title": "Test"},
            "task": {"bug_id": task["id"]},
        }

    monkeypatch.setattr(
        ingestion_run, "fetch_bug_and_task", fake_fetch
    )

    monkeypatch.setattr(
        ingestion_run,
        "save_bug_and_task",
        lambda bug, task: None,
    )

    with pytest.raises(RuntimeError, match="Launchpad request failed"):
        ingestion_run.run()

    assert processed_tasks == [1]
