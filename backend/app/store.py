import json

from . import artifacts
from .db import Record, Session


def get(identity):
    with Session() as session:
        row = session.get(Record, identity)
        if not row:
            return None
        value = json.loads(row.body)
        for metadata in value.get("artifacts", []):
            value[metadata["name"]] = artifacts.read(identity, metadata["name"])
        return value


def save(identity, kind, body):
    body = dict(body)
    if kind == "attempt":
        metadata = []
        for name in ("events", "diff"):
            if name in body:
                metadata.append(artifacts.write(identity, name, body.pop(name)))
        if metadata:
            body["artifacts"] = metadata
    with Session.begin() as session:
        row = session.get(Record, identity)
        if row:
            row.body = json.dumps(body)
            row.revision += 1
        else:
            session.add(Record(id=identity, kind=kind, body=json.dumps(body)))


def listing(kind, offset=0, limit=50):
    from sqlalchemy import select

    with Session() as session:
        rows = session.scalars(
            select(Record)
            .where(Record.kind == kind)
            .order_by(Record.updated.desc())
            .offset(offset)
            .limit(limit)
        )
        return [json.loads(row.body) for row in rows]
