from pathlib import Path
from src.transformation.validation import (
    validate_bugs,
    validate_bug_tasks,
)

from src.database import get_connection


def transform_bugs(conn):

    cursor = conn.execute("""
    INSERT INTO bugs (
                id,
                title,
                date_created,
                date_last_updated,
                information_type,
                heat,
                is_private,
                security_related,
                users_affected_count,
                tags,
                web_link
     )
     SELECT
                id,
                source_data->>'title',
                (source_data->>'date_created')::TIMESTAMPTZ,
                (source_data->>'date_last_updated')::TIMESTAMPTZ,
                source_data->>'information_type',
                (source_data->>'heat')::INTEGER,
                (source_data->>'private')::BOOLEAN,
                (source_data->>'security_related')::BOOLEAN,
                (source_data->>'users_affected_count')::INTEGER,
                ARRAY(
                    SELECT jsonb_array_elements_text(source_data->'tags')
     ),
     source_data->>'web_link'
     FROM raw_bugs
           ON CONFLICT (id)
            DO UPDATE SET
                title = EXCLUDED.title,
                date_created = EXCLUDED.date_created,
                date_last_updated = EXCLUDED.date_last_updated,
                information_type = EXCLUDED.information_type,
                heat = EXCLUDED.heat,
                is_private = EXCLUDED.is_private,
                security_related = EXCLUDED.security_related,
                users_affected_count = EXCLUDED.users_affected_count,
                tags = EXCLUDED.tags,
                web_link = EXCLUDED.web_link
     """)
    return cursor.rowcount


def transform_bug_tasks(conn):
    cursor = conn.execute("""
            INSERT INTO bug_tasks (
                task_url,
                bug_id,
                bug_target_name,
                status,
                importance,
                is_complete,
                date_created,
                date_closed,
                date_fix_released
            )
            SELECT
                task_url,
                bug_id,
                bug_target_name,
                source_data->>'status',
                source_data->>'importance',
                (source_data->>'is_complete')::BOOLEAN,
                (source_data->>'date_created')::TIMESTAMPTZ,
                (source_data->>'date_closed')::TIMESTAMPTZ,
                (source_data->>'date_fix_released')::TIMESTAMPTZ
            FROM raw_bug_tasks
            ON CONFLICT (task_url)
            DO UPDATE SET
                bug_id = EXCLUDED.bug_id,
                bug_target_name = EXCLUDED.bug_target_name,
                status = EXCLUDED.status,
                importance = EXCLUDED.importance,
                is_complete = EXCLUDED.is_complete,
                date_created = EXCLUDED.date_created,
                date_closed = EXCLUDED.date_closed,
                date_fix_released = EXCLUDED.date_fix_released
            """)
    return cursor.rowcount


def run_transformations():
    with get_connection() as conn:
        bug_count = transform_bugs(conn)
        task_count = transform_bug_tasks(conn)
        print(f"Transformed bugs: {bug_count}")
        print(f"Transformed bug tasks: {task_count}")
        
        validate_bugs(conn)
        validate_bug_tasks(conn)
        
        create_analytics_views(conn)


def create_analytics_views(conn):
    sql_file = Path(__file__).with_name("views.sql")
    sql = sql_file.read_text()

    conn.execute(sql)

if __name__ == "__main__":
    run_transformations()
    print("All transformations completed successfully.")
