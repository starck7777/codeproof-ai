import pytest
from app import db, store
from app.main import rate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr("app.artifacts.ROOT", tmp_path / "artifacts")
    engine = create_engine("sqlite:///" + str(tmp_path / "test.db"))
    db.Base.metadata.create_all(engine)
    monkeypatch.setattr(store, "Session", sessionmaker(engine, expire_on_commit=False))
    rate.clear()
    yield engine
    engine.dispose()
