CREATE TABLE IF NOT EXISTS raw_bugs (
    id BIGINT PRIMARY KEY,
    source_data JSONB NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_bug_tasks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    bug_id BIGINT NOT NULL REFERENCES raw_bugs(id),
    bug_target_name TEXT NOT NULL,
    source_data JSONB NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    task_url TEXT NOT NULL UNIQUE,
    etag TEXT
);

