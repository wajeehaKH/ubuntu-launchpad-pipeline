def validate_bugs(conn):
    cursor = conn.execute("""
        SELECT
            COUNT(*) AS total_bugs,
            COUNT(*) FILTER (
                WHERE title IS NULL
            ) AS missing_titles,
            COUNT(*) FILTER (
                WHERE date_created IS NULL
            ) AS missing_creation_dates
        FROM bugs
    """)

    total, missing_titles, missing_dates = cursor.fetchone()

    if missing_titles or missing_dates:
        raise ValueError(
            f"Bug validation failed: "
            f"{missing_titles} missing titles, "
            f"{missing_dates} missing creation dates"
        )

    print(f"Bug validation passed: {total} records checked.")

def validate_bug_tasks(conn):
    cursor = conn.execute("""
        SELECT
            COUNT(*) AS total_tasks,
            COUNT(*) FILTER (
                WHERE task_url IS NULL
            ) AS missing_task_urls,
            COUNT(*) FILTER (
                WHERE bug_id IS NULL
            ) AS missing_bug_ids,
            COUNT(*) FILTER (
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM bugs b
                    WHERE b.id = bug_tasks.bug_id
                )
            ) AS orphaned_tasks
        FROM bug_tasks
    """)

    total, missing_urls, missing_bug_ids, orphaned = cursor.fetchone()

    if missing_urls or missing_bug_ids or orphaned:
        raise ValueError(
            f"Task validation failed: "
            f"{missing_urls} missing URLs, "
            f"{missing_bug_ids} missing bug IDs, "
            f"{orphaned} orphaned tasks"
        )

    print(f"Task validation passed: {total} records checked.")
