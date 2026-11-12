import json

import pytest
from app import store
from app.catalog import TASKS, tasks
from app.main import app
from app.metrics import aggregate, price
from app.sandbox import Sandbox
from app.security import gateway_url, patch_source, redact, safe_path
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.mark.parametrize(
    "path", ["../hidden/test.py", "/etc/passwd", "a/../../x", "a\\b", "x\x00y"]
)
def test_traversal(tmp_path, path):
    with pytest.raises(ValueError):
        safe_path(tmp_path, path)


def test_symlink_and_protected(tmp_path):
    (tmp_path / "escape").symlink_to("/tmp")
    with pytest.raises(ValueError):
        safe_path(tmp_path, "escape/a")
    with pytest.raises(ValueError):
        patch_source(tmp_path, "tests/test.py", "malicious")
    with pytest.raises(ValueError):
        patch_source(tmp_path, "solution.py", "x" * 32769)
    patch_source(tmp_path, "solution.py", "def solve(): pass")
    assert (tmp_path / "solution.py").read_text() == "def solve(): pass"


def test_gateway_ssrf(monkeypatch):
    monkeypatch.setenv("BIFROST_URL", "http://169.254.169.254")
    with pytest.raises(ValueError):
        gateway_url()
    monkeypatch.setenv("BIFROST_URL", "http://127.0.0.1:8080")
    assert gateway_url() == "http://127.0.0.1:8080"
    monkeypatch.setenv(
        "BIFROST_URL",
        "http://user:password@127.0.0.1:8080",  # pragma: allowlist secret
    )  # pragma: allowlist secret - invalid URL fixture
    with pytest.raises(ValueError):
        gateway_url()


def test_redaction(monkeypatch):
    monkeypatch.setenv(
        "BIFROST_VIRTUAL_KEY", "fixture-secret-value"
    )  # pragma: allowlist secret - synthetic test value
    assert "fixture-secret-value" not in redact("value fixture-secret-value")
    assert "unsafe" not in redact("Authorization: unsafe")


def test_catalog_has_twelve_original_tasks():
    assert len(tasks()) == 12
    assert {t["difficulty"] for t in tasks()} == {"easy", "medium", "hard"}
    for t in tasks():
        root = TASKS / t["id"]
        assert t["editable"] == ["solution.py"]
        for category in ("public", "hidden", "regression"):
            assert json.loads((root / category / "cases.json").read_text())
        assert (root / "starter/solution.py").read_text() != (
            root / "reference/solution.py"
        ).read_text()


def test_no_docker_no_execution(monkeypatch, tmp_path):
    monkeypatch.setattr("app.sandbox.shutil.which", lambda _: None)
    with pytest.raises(RuntimeError, match="Docker unavailable"):
        Sandbox().run(tmp_path, tmp_path)


def example(success=True):
    return {
        "evaluation": {
            "success": success,
            "hidden": {"passed": 2 if success else 1, "total": 2},
            "regression": {"passed": 1, "total": 1},
        },
        "cost": 2.0,
        "tokens": 10,
        "duration": 3,
    }


def test_metrics_missing_zero_no_success_and_infrastructure():
    assert aggregate([])["success_rate"] is None
    assert aggregate([example(False)])["cost_per_success"] is None
    assert aggregate([example(), example(False)])["cost_per_success"] == 4
    a = example()
    a["tokens"] = None
    a["cost"] = None
    assert aggregate([a])["total_tokens"] is None
    assert aggregate([a])["total_cost"] is None
    a["tokens"] = 0
    a["cost"] = 0
    assert aggregate([a])["total_tokens"] == 0
    assert aggregate([a])["cost_per_success"] == 0
    a["failure_category"] = "infrastructure"
    assert aggregate([a])["valid"] == 0
    assert aggregate([a])["infrastructure_failures"] == 1
    assert price(None, {}) is None
    assert (
        price(
            {"prompt_tokens": 1000000, "completion_tokens": 500000},
            {"input_per_million": 2, "output_per_million": 4},
        )
        == 4
    )


@pytest.mark.parametrize(
    "body",
    [
        {"title": "x", "task_ids": [], "strategies": ["DirectPatch"]},
        {"title": "x", "task_ids": ["missing"], "strategies": ["DirectPatch"]},
        {"title": "x", "task_ids": ["inclusive-range"], "strategies": ["unknown"]},
        {
            "title": "x",
            "task_ids": ["inclusive-range"],
            "strategies": ["DirectPatch"],
            "budget": {"seconds": 0},
        },
        {
            "title": "x",
            "task_ids": ["inclusive-range"],
            "strategies": ["DirectPatch"],
            "unexpected": True,
        },
        {
            "title": "x",
            "task_ids": ["inclusive-range"],
            "strategies": ["DirectPatch"],
            "budget": {"tokens": "1000"},
        },
    ],
)
def test_api_validation(body):
    assert client.post("/api/runs", json=body).status_code == 422


def test_api_security_and_fail_closed(monkeypatch):
    assert client.get("/api/tasks").status_code == 200
    assert client.get("/api/tasks?offset=-1").status_code == 422
    assert client.get("/api/tasks", headers={"Host": "evil.example"}).status_code == 400
    assert (
        client.post("/api/agents", json={}, headers={"Origin": "https://evil.example"}).status_code
        == 403
    )
    assert client.post("/api/agents", content="x" * 65537).status_code == 413
    monkeypatch.setattr("app.main.shutil.which", lambda _: None)
    response = client.post(
        "/api/runs",
        json={"title": "x", "task_ids": ["inclusive-range"], "strategies": ["DirectPatch"]},
    )
    assert response.status_code == 503
    assert "host" in response.json()["detail"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert client.get("/api/runs/missing").status_code == 404
    assert (
        "access-control-allow-origin"
        not in client.get("/api/tasks", headers={"Origin": "https://evil.example"}).headers
    )


def test_rate_limit():
    for _ in range(12):
        client.post("/api/agents", json={"name": "test", "strategy": "DirectPatch"})
    assert (
        client.post("/api/agents", json={"name": "test", "strategy": "DirectPatch"}).status_code
        == 429
    )


def test_persistence_and_parameterized_queries():
    identity = "'; DROP TABLE records;--"
    store.save(identity, "agent", {"test": True})
    assert store.get(identity) == {"test": True}
    store.save(identity, "agent", {"test": False})
    assert store.listing("agent")[0] == {"test": False}


def test_exports_separation_cancellation_and_sse():
    a = example() | {
        "id": "a",
        "kind": "attempt",
        "task_id": "inclusive-range",
        "task_version": "1.0.0",
        "model": "demo/scripted",
        "strategy": "DirectPatch",
        "status": "Completed",
        "mode": "demo",
        "events": [],
        "run_id": "r",
    }
    store.save("a", "attempt", a)
    for mode in ("demo", "live"):
        identity = "r" if mode == "demo" else "l"
        store.save(
            identity,
            "run",
            {
                "id": identity,
                "kind": "run",
                "title": "<script>alert(1)</script>",
                "mode": mode,
                "created": 0,
                "attempt_ids": ["a"] if mode == "demo" else [],
                "configuration": {},
                "cancelled": False,
            },
        )
    groups = client.get("/api/compare").json()["groups"]
    assert len(groups["demo"]) == len(groups["live"]) == 1
    assert client.get("/api/runs/r/report/json").json()["mode"] == "demo"
    html = client.get("/api/runs/r/report/html").text
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "inclusive-range" in client.get("/api/runs/r/report/csv").text
    assert client.get("/api/runs/r/report/zip").status_code == 404
    assert (
        "event: snapshot" in client.get("/api/runs/r/events", headers={"Last-Event-ID": "1"}).text
    )
    assert client.post("/api/runs/r/cancel", json={}).json()["cancelled"]


@pytest.mark.docker
def test_fixture_starters_fail_references_pass():
    import shutil

    if not shutil.which("docker"):
        pytest.skip("Docker is unavailable; fixture execution not verified")
    for t in tasks():
        root = TASKS / t["id"]
        starter = []
        for category in ("public", "hidden", "regression"):
            result = Sandbox().run(root / "reference", root / category)
            assert result["passed"] == result["total"], (t["id"], category, result)
            starter.append(Sandbox().run(root / "starter", root / category))
        assert any(r["passed"] < r["total"] for r in starter), t["id"]


def test_saved_agent_versions_and_model_comparison_snapshot(monkeypatch):
    created = client.post(
        "/api/agents",
        json={"name": "Original", "strategy": "PlanVerify", "model": "openai/example"},
    ).json()
    updated = client.post(
        "/api/agents/" + created["id"],
        json={"name": "Updated", "strategy": "DirectPatch", "model": "openai/other"},
    ).json()
    assert updated["version"] == 2

    class FakeRedis:
        values = {}

        def ping(self):
            return True

        def get(self, key):
            return self.values.get(key)

        def set(self, key, value, **kwargs):
            self.values[key] = value.encode()
            return True

    connection = FakeRedis()
    monkeypatch.setattr("app.main.Redis.from_url", lambda *a, **k: connection)
    monkeypatch.setattr("app.main.shutil.which", lambda _: "/usr/bin/docker")
    queued = []

    class FakeQueue:
        def __init__(self, *a, **k):
            pass

        def enqueue(self, *a, **k):
            queued.append(k["job_id"])

    monkeypatch.setattr("app.main.Queue", FakeQueue)
    body = {
        "title": "Models",
        "task_ids": ["inclusive-range"],
        "strategies": ["DirectPatch"],
        "comparison_mode": "models",
        "models": ["provider/a", "provider/b"],
    }
    headers = {"Idempotency-Key": "test-idempotency-key-123"}
    r = client.post("/api/runs", json=body, headers=headers)
    assert r.status_code == 201
    run = r.json()
    assert len(run["attempts"]) == 2
    assert {a["model"] for a in run["attempts"]} == {"provider/a", "provider/b"}
    assert all(a["task_snapshot"]["content_digest"] for a in run["attempts"])
    assert client.post("/api/runs", json=body, headers=headers).json()["id"] == run["id"]
    assert len(queued) == 2
    assert client.post("/api/runs", json=body | {"models": ["provider/a"]}).status_code == 422
    assert client.post("/api/runs", json=body | {"budget": {"max_cost": 1.0}}).status_code == 422


def test_artifacts_are_external_and_paths_are_not_accepted(tmp_path):
    from app import artifacts, store

    store.save(
        "safe-attempt",
        "attempt",
        {"id": "safe-attempt", "events": [{"summary": "hello"}], "diff": "+fixed"},
    )
    assert store.get("safe-attempt")["diff"] == "+fixed"
    assert (artifacts.ROOT / "safe-attempt/diff.json").is_file()
    with pytest.raises(ValueError):
        artifacts.read("../outside", "diff")
    with pytest.raises(ValueError):
        artifacts.read("safe-attempt", "../credentials")
