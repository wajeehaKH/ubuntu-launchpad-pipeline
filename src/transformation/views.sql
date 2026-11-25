CREATE OR REPLACE VIEW bug_analytics AS
SELECT
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
    web_link,

    FLOOR(
        EXTRACT(
            EPOCH FROM (CURRENT_TIMESTAMP - date_created)
        ) / 86400
    )::INTEGER AS days_since_created,

    FLOOR(
        EXTRACT(
            EPOCH FROM (CURRENT_TIMESTAMP - date_last_updated)
        ) / 86400
    )::INTEGER AS days_since_last_update,

    date_last_updated < CURRENT_TIMESTAMP - INTERVAL '365 days'
        AS is_stale

FROM bugs;
