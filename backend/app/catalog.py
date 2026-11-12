import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "tasks"
STRATEGIES = ["DirectPatch", "IterativeFix", "PlanVerify"]


def tasks():
    values = []
    for p in sorted(TASKS.glob("*/task.json")):
        value = json.loads(p.read_text())
        digest = hashlib.sha256()
        for source in sorted(p.parent.rglob("*")):
            if source.is_file() and "__pycache__" not in source.parts:
                digest.update(str(source.relative_to(p.parent)).encode())
                digest.update(source.read_bytes())
        value["content_digest"] = digest.hexdigest()
        values.append(value)
    return values


def task(identity):
    return next((t for t in tasks() if t["id"] == identity), None)
