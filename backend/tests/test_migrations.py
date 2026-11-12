import os
import subprocess
from pathlib import Path

from sqlalchemy import create_engine, inspect


def test_migration_upgrade_downgrade_persistence(tmp_path):
    url = "sqlite:///" + str(tmp_path / "migration.db")
    env = os.environ | {"DATABASE_URL": url, "PYTHONPATH": "backend"}
    executable = str(Path(".venv/bin/alembic").resolve())
    subprocess.run(
        [executable, "-c", "backend/alembic.ini", "upgrade", "head"],
        env=env,
        check=True,
        capture_output=True,
    )
    engine = create_engine(url)
    assert "records" in inspect(engine).get_table_names()
    with engine.begin() as conn:
        from sqlalchemy import text

        conn.execute(
            text(
                "INSERT INTO records (id, kind, body, revision, updated) VALUES (:id,:kind,:body,1,CURRENT_TIMESTAMP)"
            ),
            {"id": "test", "kind": "run", "body": "{}"},
        )
    engine.dispose()
    subprocess.run(
        [executable, "-c", "backend/alembic.ini", "upgrade", "head"],
        env=env,
        check=True,
        capture_output=True,
    )
    with engine.connect() as conn:
        from sqlalchemy import text

        assert conn.scalar(text("SELECT count(*) FROM records")) == 1
    subprocess.run(
        [executable, "-c", "backend/alembic.ini", "downgrade", "base"],
        env=env,
        check=True,
        capture_output=True,
    )
    assert "records" not in inspect(engine).get_table_names()


def test_postgres_persistence_in_disposable_schema(monkeypatch):
    import uuid

    import pytest
    from app import db, store
    from sqlalchemy import text
    from sqlalchemy.orm import sessionmaker

    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip(
            "TEST_POSTGRES_URL not set; PostgreSQL check requires an isolated test database"
        )
    engine = create_engine(url)
    schema = "test_" + uuid.uuid4().hex
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA " + schema))
        scoped = engine.execution_options(schema_translate_map={None: schema})
        db.Base.metadata.create_all(scoped)
        monkeypatch.setattr(store, "Session", sessionmaker(scoped, expire_on_commit=False))
        store.save("durable", "run", {"snapshot": {"tokens": 42}})
        assert store.get("durable")["snapshot"]["tokens"] == 42
        assert store.listing("run")[0]["snapshot"]["tokens"] == 42
    finally:
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA IF EXISTS " + schema + " CASCADE"))
        engine.dispose()
