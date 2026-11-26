import pytest
import psycopg

from src.transformation.transform import transform_bug_tasks

from psycopg.types.json import Jsonb

from src.transformation.transform import transform_bugs

from src.transformation.validation import validate_bugs

from src.transformation.validation import validate_bug_tasks

from datetime import datetime, timedelta, timezone

def test_transform_bugs_extracts_raw_data(db_connection):
    raw_bug = {
        "title": "Test Ubuntu bug",
        "date_created": "2025-01-10T10:00:00+00:00",
        "date_last_updated": "2025-02-10T10:00:00+00:00",
        "information_type": "PUBLIC",
        "heat": 5,
        "private": False,
        "security_related": False,
        "users_affected_count": 3,
        "tags": ["ubuntu", "testing"],
        "web_link": "https://bugs.launchpad.net/bugs/999999",
    }

    db_connection.execute(
        """
        INSERT INTO raw_bugs (id, source_data)
        VALUES (%s, %s)
        """,
        (999999, Jsonb(raw_bug)),
    )

    affected_rows = transform_bugs(db_connection)

    result = db_connection.execute(
        """
        SELECT title, heat, is_private, tags
        FROM bugs
        WHERE id = %s
        """,
        (999999,),
    ).fetchone()

    assert affected_rows == 1
    assert result == (
        "Test Ubuntu bug",
        5,
        False,
        ["ubuntu", "testing"],
    )


def test_transform_bugs_updates_existing_record(db_connection):
    raw_bug = {
        "title": "Original title",
        "date_created": "2025-01-10T10:00:00+00:00",
        "date_last_updated": "2025-02-10T10:00:00+00:00",
        "information_type": "PUBLIC",
        "heat": 5,
        "private": False,
        "security_related": False,
        "users_affected_count": 3,
        "tags": ["ubuntu"],
        "web_link": "https://bugs.launchpad.net/bugs/999998",
    }

    db_connection.execute(
        """
        INSERT INTO raw_bugs (id, source_data)
        VALUES (%s, %s)
        """,
        (999998, Jsonb(raw_bug)),
    )

    transform_bugs(db_connection)

    raw_bug["title"] = "Updated title"
    raw_bug["heat"] = 10

    db_connection.execute(
        """
        UPDATE raw_bugs
        SET source_data = %s
        WHERE id = %s
        """,
        (Jsonb(raw_bug), 999998),
    )

    affected_rows = transform_bugs(db_connection)

    result = db_connection.execute(
        """
        SELECT title, heat
        FROM bugs
        WHERE id = %s
        """,
        (999998,),
    ).fetchone()

    assert affected_rows == 1
    assert result == ("Updated title", 10)


def test_transform_bugs_is_idempotent(db_connection):
    raw_bug = {
        "title": "Idempotency test",
        "date_created": "2025-01-10T10:00:00+00:00",
        "date_last_updated": "2025-02-10T10:00:00+00:00",
        "information_type": "PUBLIC",
        "heat": 5,
        "private": False,
        "security_related": False,
        "users_affected_count": 3,
        "tags": ["testing"],
        "web_link": "https://bugs.launchpad.net/bugs/999997",
    }

    db_connection.execute(
        """
        INSERT INTO raw_bugs (id, source_data)
        VALUES (%s, %s)
        """,
        (999997, Jsonb(raw_bug)),
    )

    transform_bugs(db_connection)
    transform_bugs(db_connection)

    result = db_connection.execute(
        """
        SELECT COUNT(*)
        FROM bugs
        WHERE id = %s
        """,
        (999997,),
    ).fetchone()[0]

    assert result == 1

def test_transform_bug_tasks_extracts_raw_data(db_connection):
    raw_bug = {
        "title": "Parent bug",
        "date_created": "2025-01-10T10:00:00+00:00",
        "date_last_updated": "2025-02-10T10:00:00+00:00",
        "information_type": "PUBLIC",
        "heat": 5,
        "private": False,
        "security_related": False,
        "users_affected_count": 3,
        "tags": [],
        "web_link": "https://bugs.launchpad.net/bugs/999996",
    }

    db_connection.execute(
        """
        INSERT INTO raw_bugs (id, source_data)
        VALUES (%s, %s)
        """,
        (999996, Jsonb(raw_bug)),
    )

    transform_bugs(db_connection)

    raw_task = {
        "status": "New",
        "importance": "High",
        "is_complete": False,
        "date_created": "2025-01-10T11:00:00+00:00",
        "date_closed": None,
        "date_fix_released": None,
    }

    db_connection.execute(
        """
        INSERT INTO raw_bug_tasks (
            bug_id,
            task_url,
            bug_target_name,
            source_data
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            999996,
            "https://api.launchpad.net/1.0/ubuntu/+bug/999996",
            "test-package (Ubuntu)",
            Jsonb(raw_task),
        ),
    )

    affected_rows = transform_bug_tasks(db_connection)

    result = db_connection.execute(
        """
        SELECT bug_id, status, importance, is_complete
        FROM bug_tasks
        WHERE bug_id = %s
        """,
        (999996,),
    ).fetchone()

    assert affected_rows == 1
    assert result == (999996, "New", "High", False)

def test_bug_task_rejects_missing_parent_bug(db_connection):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        db_connection.execute(
            """
            INSERT INTO bug_tasks (
                task_url,
                bug_id,
                bug_target_name
            )
            VALUES (%s, %s, %s)
            """,
            (
                "https://api.launchpad.net/1.0/ubuntu/+bug/999995",
                999995,
                "missing-package (Ubuntu)",
            ),
        )


def test_validate_bugs_rejects_missing_creation_date(db_connection):
    db_connection.execute(
        """
        INSERT INTO bugs (id, title, date_created)
        VALUES (%s, %s, %s)
        """,
        (999994, "Bug without creation date", None),
    )

    with pytest.raises(ValueError, match="missing creation dates"):
        validate_bugs(db_connection)


def test_transform_bug_tasks_updates_existing_record(db_connection):
    raw_bug = {
        "title": "Parent bug",
        "date_created": "2025-01-10T10:00:00+00:00",
        "date_last_updated": "2025-02-10T10:00:00+00:00",
        "information_type": "PUBLIC",
        "heat": 5,
        "private": False,
        "security_related": False,
        "users_affected_count": 3,
        "tags": [],
        "web_link": "https://bugs.launchpad.net/bugs/999992",
    }

    db_connection.execute(
        """
        INSERT INTO raw_bugs (id, source_data)
        VALUES (%s, %s)
        """,
        (999992, Jsonb(raw_bug)),
    )

    transform_bugs(db_connection)

    raw_task = {
        "status": "New",
        "importance": "High",
        "is_complete": False,
        "date_created": "2025-01-10T11:00:00+00:00",
        "date_closed": None,
        "date_fix_released": None,
    }

    task_url = "https://api.launchpad.net/1.0/ubuntu/+bug/999992"

    db_connection.execute(
        """
        INSERT INTO raw_bug_tasks (
            bug_id, task_url, bug_target_name, source_data
        )
        VALUES (%s, %s, %s, %s)
        """,
        (999992, task_url, "test-package (Ubuntu)", Jsonb(raw_task)),
    )

    transform_bug_tasks(db_connection)

    raw_task["status"] = "Fix Released"
    raw_task["is_complete"] = True

    db_connection.execute(
        """
        UPDATE raw_bug_tasks
        SET source_data = %s
        WHERE task_url = %s
        """,
        (Jsonb(raw_task), task_url),
    )

    affected_rows = transform_bug_tasks(db_connection)

    result = db_connection.execute(
        """
        SELECT status, is_complete
        FROM bug_tasks
        WHERE task_url = %s
        """,
        (task_url,),
    ).fetchone()

    assert affected_rows == 1
    assert result == ("Fix Released", True)


def test_transform_bug_tasks_is_idempotent(db_connection):
    raw_bug = {
        "title": "Parent bug",
        "date_created": "2025-01-10T10:00:00+00:00",
        "date_last_updated": "2025-02-10T10:00:00+00:00",
        "information_type": "PUBLIC",
        "heat": 5,
        "private": False,
        "security_related": False,
        "users_affected_count": 3,
        "tags": [],
        "web_link": "https://bugs.launchpad.net/bugs/999991",
    }

    db_connection.execute(
        """
        INSERT INTO raw_bugs (id, source_data)
        VALUES (%s, %s)
        """,
        (999991, Jsonb(raw_bug)),
    )

    transform_bugs(db_connection)

    raw_task = {
        "status": "New",
        "importance": "High",
        "is_complete": False,
        "date_created": "2025-01-10T11:00:00+00:00",
        "date_closed": None,
        "date_fix_released": None,
    }

    task_url = "https://api.launchpad.net/1.0/ubuntu/+bug/999991"

    db_connection.execute(
        """
        INSERT INTO raw_bug_tasks (
            bug_id, task_url, bug_target_name, source_data
        )
        VALUES (%s, %s, %s, %s)
        """,
        (999991, task_url, "test-package (Ubuntu)", Jsonb(raw_task)),
    )

    first_count = transform_bug_tasks(db_connection)
    second_count = transform_bug_tasks(db_connection)

    total = db_connection.execute(
        """
        SELECT COUNT(*)
        FROM bug_tasks
        WHERE task_url = %s
        """,
        (task_url,),
    ).fetchone()[0]

    assert first_count == 1
    assert second_count == 1
    assert total == 1

def test_validate_bug_tasks_passes_with_valid_data(db_connection):
    raw_bug = {
        "title": "Parent bug",
        "date_created": "2025-01-10T10:00:00+00:00",
        "date_last_updated": "2025-02-10T10:00:00+00:00",
        "information_type": "PUBLIC",
        "heat": 5,
        "private": False,
        "security_related": False,
        "users_affected_count": 3,
        "tags": [],
        "web_link": "https://bugs.launchpad.net/bugs/999990",
    }

    db_connection.execute(
        """
        INSERT INTO raw_bugs (id, source_data)
        VALUES (%s, %s)
        """,
        (999990, Jsonb(raw_bug)),
    )

    transform_bugs(db_connection)

    task_url = "https://api.launchpad.net/1.0/ubuntu/+bug/999990"

    db_connection.execute(
        """
        INSERT INTO bug_tasks (
            task_url, bug_id, bug_target_name, status, importance,
            is_complete
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            task_url, 999990, "test-package (Ubuntu)",
            "New", "High", False,
        ),
    )

    validate_bug_tasks(db_connection)


def test_bug_analytics_view_calculates_metrics(db_connection):
    now = datetime.now(timezone.utc)

    old_bug = {
        "title": "Old bug",
        "date_created": (now - timedelta(days=500)).isoformat(),
        "date_last_updated": (now - timedelta(days=400)).isoformat(),
        "information_type": "PUBLIC",
        "heat": 5,
        "private": False,
        "security_related": False,
        "users_affected_count": 3,
        "tags": [],
        "web_link": "https://bugs.launchpad.net/bugs/999989",
    }

    recent_bug = {
        **old_bug,
        "title": "Recently updated bug",
        "date_created": (now - timedelta(days=100)).isoformat(),
        "date_last_updated": (now - timedelta(days=10)).isoformat(),
        "web_link": "https://bugs.launchpad.net/bugs/999988",
    }

    db_connection.execute(
        """
        INSERT INTO raw_bugs (id, source_data)
        VALUES (%s, %s), (%s, %s)
        """,
        (999989, Jsonb(old_bug), 999988, Jsonb(recent_bug)),
    )

    transform_bugs(db_connection)

    results = db_connection.execute(
        """
        SELECT id, days_since_created, days_since_last_update, is_stale
        FROM bug_analytics
        WHERE id IN (%s, %s)
        ORDER BY id DESC
        """,
        (999989, 999988),
    ).fetchall()

    old_result, recent_result = results

    assert old_result[0] == 999989
    assert old_result[1] >= 499
    assert old_result[2] >= 399
    assert old_result[3] is True

    assert recent_result[0] == 999988
    assert recent_result[1] >= 99
    assert recent_result[2] >= 9
    assert recent_result[3] is False
