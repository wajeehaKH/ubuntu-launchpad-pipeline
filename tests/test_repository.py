from src.ingestion.repository import _save_bug
import os
import psycopg
import pytest

from src.ingestion.repository import save_bug_and_task


def test_save_bug_inserts_raw_bug(db_connection):
    bug = {
        "id": 999980,
        "title": "Repository test bug",
    }

    _save_bug(db_connection, bug)

    result = db_connection.execute(
        """
        SELECT id, source_data->>'title'
        FROM raw_bugs
        WHERE id = %s
        """,
        (999980,),
    ).fetchone()

    assert result == (999980, "Repository test bug")


from src.ingestion.repository import _save_bug_task


def test_save_bug_task_inserts_raw_task(db_connection):
    bug = {
        "title": "Parent bug",
        "date_created": "2025-01-10T10:00:00+00:00",
        "date_last_updated": "2025-02-10T10:00:00+00:00",
        "information_type": "PUBLIC",
        "heat": 5,
        "private": False,
        "security_related": False,
        "users_affected_count": 3,
        "tags": [],
        "web_link": "https://bugs.launchpad.net/bugs/999979",
    }

    from psycopg.types.json import Jsonb

    db_connection.execute(
        """
        INSERT INTO raw_bugs (id, source_data)
        VALUES (%s, %s)
        """,
        (999979, Jsonb(bug)),
    )

    task = {
        "bug_id": 999979,
        "self_link": "https://api.launchpad.net/1.0/ubuntu/+bug/999979",
        "bug_target_name": "test-package (Ubuntu)",
        "status": "New",
        "importance": "High",
        "http_etag": '"abc123"',
    }

    _save_bug_task(db_connection, task)

    result = db_connection.execute(
        """
        SELECT bug_id, task_url, bug_target_name, etag,
               source_data->>'status'
        FROM raw_bug_tasks
        WHERE task_url = %s
        """,
        (task["self_link"],),
    ).fetchone()

    assert result == (
        999979,
        task["self_link"],
        "test-package (Ubuntu)",
        '"abc123"',
        "New",
    )


def test_save_bug_updates_existing_record(db_connection):
    bug = {
        "id": 999978,
        "title": "Original title",
    }

    _save_bug(db_connection, bug)

    bug["title"] = "Updated title"

    _save_bug(db_connection, bug)

    result = db_connection.execute(
        """
        SELECT COUNT(*), MAX(source_data->>'title')
        FROM raw_bugs
        WHERE id = %s
        """,
        (999978,),
    ).fetchone()

    assert result == (1, "Updated title")


def test_save_bug_task_updates_existing_record(db_connection):
    from psycopg.types.json import Jsonb

    bug = {"title": "Parent bug"}

    db_connection.execute(
        """
        INSERT INTO raw_bugs (id, source_data)
        VALUES (%s, %s)
        """,
        (999977, Jsonb(bug)),
    )

    task = {
        "bug_id": 999977,
        "self_link": "https://api.launchpad.net/1.0/ubuntu/+bug/999977",
        "bug_target_name": "test-package (Ubuntu)",
        "status": "New",
        "importance": "High",
        "http_etag": '"etag-1"',
    }

    _save_bug_task(db_connection, task)

    task["status"] = "Fix Released"
    task["http_etag"] = '"etag-2"'

    _save_bug_task(db_connection, task)

    result = db_connection.execute(
        """
        SELECT COUNT(*), MAX(source_data->>'status'), MAX(etag)
        FROM raw_bug_tasks
        WHERE task_url = %s
        """,
        (task["self_link"],),
    ).fetchone()

    assert result == (1, "Fix Released", '"etag-2"')


def test_save_bug_and_task_rolls_back_on_task_failure(
    db_connection, test_database, monkeypatch
):
    import src.ingestion.repository as repository

    monkeypatch.setattr(
        repository,
        "get_connection",
        lambda: psycopg.connect(
            host="postgres",
            port=5432,
            dbname=test_database,
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
        ),
    )

    bug = {
        "id": 999976,
        "title": "Transaction rollback test",
    }

    task = {
        "bug_id": 999975,  # Deliberately nonexistent parent
        "self_link": "https://api.launchpad.net/1.0/ubuntu/+bug/999976",
        "bug_target_name": "test-package (Ubuntu)",
        "status": "New",
        "importance": "High",
    }

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        save_bug_and_task(bug, task)

    result = db_connection.execute(
        "SELECT COUNT(*) FROM raw_bugs WHERE id = %s",
        (999976,),
    ).fetchone()[0]

    assert result == 0
