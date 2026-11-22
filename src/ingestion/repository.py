
from psycopg.types.json import Jsonb

from src.database import get_connection


def _save_bug(conn, bug):
    conn.execute(
        """
        INSERT INTO raw_bugs (id, source_data)
        VALUES (%s, %s)
        ON CONFLICT (id)
        DO UPDATE SET
            source_data = EXCLUDED.source_data,
            ingested_at = NOW()
        """,
        (bug["id"], Jsonb(bug)),
    )


def _save_bug_task(conn, task):
    conn.execute(
        """
        INSERT INTO raw_bug_tasks (
            bug_id,
            task_url,
            bug_target_name,
            source_data,
	    etag
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (task_url)
        DO UPDATE SET
            bug_id = EXCLUDED.bug_id,
            bug_target_name = EXCLUDED.bug_target_name,
            source_data = EXCLUDED.source_data,
            etag = EXCLUDED.etag,
            ingested_at = NOW()
        """,
        (
            task["bug_id"],
            task["self_link"],
            task["bug_target_name"],
            Jsonb(task),
            task.get("http_etag")
        ),
    )


def save_bug_and_task(bug, task):
    with get_connection() as conn:
        _save_bug(conn, bug)
        _save_bug_task(conn, task)
