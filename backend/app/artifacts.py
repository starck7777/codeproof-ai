"""Bounded, atomic artifacts outside database rows. No user-provided paths."""

import json
import os
import re
import tempfile
from pathlib import Path

ROOT = Path(os.getenv("ARTIFACT_ROOT", str(Path(__file__).resolve().parents[2] / "artifacts")))


def directory(identity):
    if not re.fullmatch(r"[a-zA-Z0-9-]{1,64}", identity):
        raise ValueError("invalid artifact identity")
    root = ROOT.resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = root / identity
    if path.is_symlink():
        raise ValueError("symlink artifact directory")
    path.mkdir(exist_ok=True)
    return path


def write(identity, name, value):
    if name not in ("events", "diff"):
        raise ValueError("unknown artifact")
    content = json.dumps(value)
    if len(content.encode()) > 2_000_000:
        raise ValueError("artifact output limit")
    path = directory(identity) / (name + ".json")
    if path.is_symlink():
        raise ValueError("symlink artifact")
    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, suffix=".tmp", delete=False
    ) as output:
        temporary = Path(output.name)
        output.write(content)
    temporary.chmod(0o644)
    temporary.replace(path)
    return {"name": name, "bytes": len(content.encode()), "format": "json"}


def read(identity, name):
    if name not in ("events", "diff"):
        raise ValueError("unknown artifact")
    path = directory(identity) / (name + ".json")
    if path.is_symlink() or path.stat().st_size > 2_000_000:
        raise ValueError("unsafe artifact")
    return json.loads(path.read_text())
