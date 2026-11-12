import json
import subprocess
import time

import pytest
from app import store
from app.recovery import recover
from app.sandbox import Sandbox
from app.worker import execute


def test_duplicate_delivery_terminal_ignored():
    store.save("done", "attempt", {"id": "done", "status": "Completed"})
    execute("done")
    assert store.get("done")["status"] == "Completed"


def test_recovery_does_not_grant_repair_retry(monkeypatch):
    class FakeRedis:
        def exists(self, _):
            return False

    monkeypatch.setattr("app.recovery.Redis.from_url", lambda _: FakeRedis())
    store.save("r", "run", {"id": "r", "created": 0, "attempt_ids": ["a"]})
    store.save("a", "attempt", {"id": "a", "status": "Evaluating", "budget": {"seconds": 10}})
    assert recover() == ["a"]
    a = store.get("a")
    assert a["status"] == "Failed" and a["failure_category"] == "infrastructure"
    assert recover() == []


@pytest.mark.docker
def test_hidden_inaccessible_offline_nonroot_and_no_credentials(tmp_path):
    work = tmp_path / "source"
    work.mkdir()
    work.chmod(0o755)
    tests = tmp_path / "public"
    tests.mkdir()
    (work / "solution.py").write_text("""import os,socket
from pathlib import Path
def solve():
    forbidden=['/var/run/docker.sock','/root/.aws','/tasks','/trusted/hidden','/candidate/../hidden']
    clean=all(not os.access(p, os.R_OK) for p in forbidden)
    credentials=not any(k in os.environ for k in ['BIFROST_VIRTUAL_KEY','OPENAI_API_KEY','BIFROST_AUTHORIZATION'])
    try:
        socket.create_connection(('1.1.1.1',443),timeout=.2)
        offline=False
    except OSError:
        offline=True
    try:
        Path('/root-write-probe').write_text('x')
        readonly=False
    except OSError:
        readonly=True
    return clean and credentials and offline and readonly and os.getuid()!=0
""")
    (tests / "cases.json").write_text(json.dumps([[[], True]]))
    assert Sandbox().run(work, tests) == {"passed": 1, "total": 1}


@pytest.mark.docker
@pytest.mark.parametrize("reason", ["cancel", "deadline"])
def test_cancellation_timeout_cleanup(tmp_path, reason, monkeypatch):
    work = tmp_path / "source"
    work.mkdir()
    work.chmod(0o755)
    tests = tmp_path / "tests"
    tests.mkdir()
    (work / "solution.py").write_text(
        "import time\ndef solve():\n    time.sleep(30)\n    return True\n"
    )
    (tests / "cases.json").write_text("[[[],true]]")
    names = []
    real_popen = subprocess.Popen

    def record_popen(args, **kwargs):
        if "--name" in args:
            names.append(args[args.index("--name") + 1])
        return real_popen(args, **kwargs)

    monkeypatch.setattr("app.sandbox.subprocess.Popen", record_popen)
    start = time.monotonic()
    sandbox = Sandbox(
        cancelled=lambda: reason == "cancel" and time.monotonic() - start > 0.7,
        deadline=start + 0.7 if reason == "deadline" else start + 60,
    )
    with pytest.raises(InterruptedError if reason == "cancel" else TimeoutError):
        sandbox.run(work, tests)
    assert sandbox.active is None
    # Container name captured from running process is gone; no unrelated cleanup.
    listing = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True, check=True
    ).stdout
    assert not set(names).intersection(listing.splitlines())
