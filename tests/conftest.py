import os
from pathlib import Path

import psycopg
import pytest
from psycopg import sql


TEST_DB = "launchpad_pipeline_test"


@pytest.fixture(scope="session")
def test_database():
    admin_conn = psycopg.connect(
        host="postgres",
        port=5432,
        dbname="postgres",
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        autocommit=True,
    )

    try:
        if os.environ["POSTGRES_DB"] == TEST_DB:
            raise RuntimeError(
                "Test database must not be the development database."
            )

        admin_conn.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                sql.Identifier(TEST_DB)
            )
        )

        admin_conn.execute(
            sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(TEST_DB)
            )
        )

        project_root = Path(__file__).resolve().parents[1]

        schema_files = [
            project_root / "src/ingestion/schema.sql",
            project_root / "src/transformation/schema.sql",
            project_root / "src/transformation/views.sql",
        ]

        with psycopg.connect(
            host="postgres",
            port=5432,
            dbname=TEST_DB,
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
        ) as conn:
            for schema_file in schema_files:
                conn.execute(schema_file.read_text())

        yield TEST_DB

    finally:
        admin_conn.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                sql.Identifier(TEST_DB)
            )
        )
        admin_conn.close()


@pytest.fixture
def db_connection(test_database):
    conn = psycopg.connect(
        host="postgres",
        port=5432,
        dbname=test_database,
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )

    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()
