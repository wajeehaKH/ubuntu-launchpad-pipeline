
CREATE TABLE IF NOT EXISTS bugs (
    id BIGINT PRIMARY KEY,
    title TEXT NOT NULL,
    date_created TIMESTAMPTZ,
    date_last_updated TIMESTAMPTZ,
    information_type TEXT,
    heat INTEGER,
    is_private BOOLEAN,
    security_related BOOLEAN,
    users_affected_count INTEGER,
    tags TEXT[],
    web_link TEXT
);

CREATE TABLE IF NOT EXISTS bug_tasks (
    task_url TEXT PRIMARY KEY,
    bug_id BIGINT NOT NULL REFERENCES bugs(id),
    bug_target_name TEXT NOT NULL,
    status TEXT,
    importance TEXT,
    is_complete BOOLEAN,
    date_created TIMESTAMPTZ,
    date_closed TIMESTAMPTZ,
    date_fix_released TIMESTAMPTZ
);
