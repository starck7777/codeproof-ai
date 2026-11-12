import asyncio
import csv
import html
import io
import json
import os
import re
import shutil
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from redis import Redis
from redis.exceptions import RedisError
from rq import Queue, Worker
from sqlalchemy.exc import SQLAlchemyError

from . import store
from .catalog import STRATEGIES, task, tasks
from .metrics import aggregate
from .pricing import snapshot

app = FastAPI(title="CodeProof AI", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Last-Event-ID", "Idempotency-Key"],
)
rate = defaultdict(deque)


@app.middleware("http")
async def protections(request: Request, call_next):
    if request.headers.get("host", "").split(":")[0] not in {
        "localhost",
        "127.0.0.1",
        "api",
        "testserver",
    }:
        return Response("Invalid host", status_code=400)
    if request.method == "POST":
        if request.headers.get("origin") not in (
            None,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ):
            return Response("Invalid origin", status_code=403)
        size = 0
        chunks = []
        async for chunk in request.stream():
            size += len(chunk)
            if size > 65536:
                return Response("Request too large", status_code=413)
            chunks.append(chunk)
        request._body = b"".join(chunks)
        if size > 65536:
            return Response("Request too large", status_code=413)
        key = request.client.host if request.client else "local"
        now = time.monotonic()
        bucket = rate[key]
        while bucket and bucket[0] < now - 60:
            bucket.popleft()
        if len(bucket) >= 12:
            return Response("Rate limit exceeded", status_code=429)
        bucket.append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Cache-Control"] = "no-store"
    return response


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Budget(Strict):
    tokens: int = Field(default=8000, ge=256, le=64000)
    tool_calls: int = Field(default=12, ge=1, le=50)
    seconds: int = Field(default=120, ge=10, le=600)
    max_cost: float | None = Field(default=None, ge=0, le=100)


class Agent(Strict):
    name: str = Field(min_length=1, max_length=80)
    strategy: str
    model: str = Field(default="openai/gpt-4o-mini", pattern=r"^[a-zA-Z0-9._:/-]{1,120}$")


class NewRun(Strict):
    title: str = Field(min_length=1, max_length=100)
    task_ids: list[str] = Field(min_length=1, max_length=12)
    strategies: list[str] = Field(min_length=1, max_length=3)
    mode: str = "demo"
    model: str = Field(default="openai/gpt-4o-mini", pattern=r"^[a-zA-Z0-9._:/-]{1,120}$")
    comparison_mode: str = "strategies"
    models: list[str] = Field(default_factory=list, max_length=3)
    repetitions: int = Field(default=1, ge=1, le=3)
    budget: Budget = Field(default_factory=Budget)


def require(identity, kind):
    result = store.get(identity)
    if not result or result.get("kind") != kind:
        raise HTTPException(404, "Not found")
    return result


@app.get("/api/health")
def health():
    ready = {
        "database": False,
        "redis": False,
        "docker_cli": bool(shutil.which("docker")),
        "live_configured": bool(os.getenv("BIFROST_URL")),
        "worker_ready": False,
    }
    try:
        store.listing("run", limit=1)
        ready["database"] = True
    except SQLAlchemyError:
        ready["database"] = False
    try:
        connection = Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"), socket_connect_timeout=1
        )
        ready["redis"] = bool(connection.ping())
        ready["worker_ready"] = bool(Worker.all(connection=connection))
    except RedisError:
        ready["redis"] = False
    return ready


@app.get("/api/tasks")
def get_tasks(offset: int = 0, limit: int = 50):
    if offset < 0 or not 1 <= limit <= 100:
        raise HTTPException(422, "Invalid pagination")
    return tasks()[offset : offset + limit]


@app.get("/api/tasks/{identity}")
def get_task(identity: str):
    result = task(identity)
    if not result:
        raise HTTPException(404, "Not found")
    return result


@app.get("/api/agents")
def agents():
    return store.listing("agent")


@app.post("/api/agents", status_code=201)
def create_agent(body: Agent):
    if body.strategy not in STRATEGIES:
        raise HTTPException(422, "Invalid strategy")
    value = body.model_dump() | {"id": uuid.uuid4().hex, "kind": "agent", "version": 1}
    store.save(value["id"], "agent", value)
    return value


@app.post("/api/agents/{identity}")
def edit_agent(identity: str, body: Agent):
    previous = require(identity, "agent")
    if body.strategy not in STRATEGIES:
        raise HTTPException(422, "Invalid strategy")
    value = body.model_dump() | {
        "id": identity,
        "kind": "agent",
        "version": previous["version"] + 1,
    }
    store.save(identity, "agent", value)
    return value


@app.get("/api/runs")
def runs(offset: int = 0, limit: int = 50):
    if offset < 0 or not 1 <= limit <= 100:
        raise HTTPException(422, "Invalid pagination")
    return [detail(r) for r in store.listing("run", offset, limit)]


def detail(run):
    attempts = [store.get(i) for i in run["attempt_ids"]]
    groups = {}
    for a in attempts:
        key = a["strategy"] + " / " + a["model"]
        groups.setdefault(key, []).append(a)
    return run | {
        "attempts": attempts,
        "metrics": aggregate(attempts),
        "by_configuration": {key: aggregate(values) for key, values in groups.items()},
        "by_difficulty": {
            level: aggregate(
                [a for a in attempts if (a.get("task_snapshot") or {}).get("difficulty") == level]
            )
            for level in ("easy", "medium", "hard")
        },
    }


@app.post("/api/runs", status_code=201)
def create_run(body: NewRun, request: Request):
    if (
        body.mode not in ("demo", "live")
        or any(not task(t) for t in body.task_ids)
        or any(s not in STRATEGIES for s in body.strategies)
    ):
        raise HTTPException(422, "Invalid mode, task or strategy")
    if len(set(body.task_ids)) != len(body.task_ids) or len(set(body.strategies)) != len(
        body.strategies
    ):
        raise HTTPException(422, "Duplicate selections")
    if not shutil.which("docker") and not health()["worker_ready"]:
        raise HTTPException(
            503,
            "Docker unavailable. Read-only exploration enabled; generated code is never executed on the host.",
        )
    if body.mode == "live" and not os.getenv("BIFROST_URL"):
        raise HTTPException(503, "Bifrost is not configured")
    if (
        sum(
            any(
                a["status"] not in {"Completed", "Failed", "Timed Out", "Cancelled"}
                for a in r["attempts"]
            )
            for r in runs()
        )
        >= 3
    ):
        raise HTTPException(429, "Active run limit reached")
    redis = Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"), socket_connect_timeout=2
    )
    try:
        redis.ping()
    except RedisError:
        raise HTTPException(503, "Queue unavailable") from None
    if body.comparison_mode not in ("strategies", "models"):
        raise HTTPException(422, "Invalid comparison mode")
    if body.comparison_mode == "models":
        if (
            len(body.strategies) != 1
            or len(body.models) < 2
            or len(set(body.models)) != len(body.models)
            or any(not re.fullmatch(r"[a-zA-Z0-9._:/-]{1,120}", m) for m in body.models)
        ):
            raise HTTPException(
                422, "Model comparison requires one strategy and two or three distinct models"
            )
        configurations = [(body.strategies[0], m) for m in body.models]
    else:
        configurations = [(strategy, body.model) for strategy in body.strategies]
    prices = {
        model: snapshot(model) if body.mode == "live" else None for _, model in configurations
    }
    if body.budget.max_cost is not None and any(value is None for value in prices.values()):
        raise HTTPException(422, "Cost budget requires configured pricing for every model")
    dedupe = request.headers.get("Idempotency-Key")
    if dedupe:
        if not re.fullmatch(r"[a-zA-Z0-9-]{16,64}", dedupe):
            raise HTTPException(422, "Invalid idempotency key")
        previous = redis.get("start:" + dedupe)
        if previous:
            existing = store.get(previous.decode())
            if existing:
                return detail(existing)
            raise HTTPException(409, "Benchmark creation in progress")
    identity = uuid.uuid4().hex
    if dedupe and not redis.set("start:" + dedupe, identity, nx=True, ex=86400):
        raise HTTPException(409, "Duplicate benchmark start")
    run = {
        "id": identity,
        "kind": "run",
        "created": time.time(),
        "configuration": body.model_dump(),
        "mode": body.mode,
        "title": body.title,
        "attempt_ids": [],
        "cancelled": False,
    }
    for t in body.task_ids:
        for strategy, model in configurations:
            for repetition in range(body.repetitions):
                a = {
                    "id": uuid.uuid4().hex,
                    "kind": "attempt",
                    "run_id": identity,
                    "task_id": t,
                    "task_version": task(t)["version"],
                    "environment": task(t)["environment"],
                    "strategy": strategy,
                    "model": model,
                    "mode": body.mode,
                    "repetition": repetition,
                    "budget": body.budget.model_dump(),
                    "status": "Queued",
                    "events": [],
                    "tool_calls": 0,
                    "tool_errors": 0,
                    "patch_revisions": 0,
                    "tokens": None,
                    "cost": None,
                    "evaluation": None,
                    "diff": "",
                    "retry": 0,
                    "pricing": prices[model],
                    "task_snapshot": task(t),
                }
                run["attempt_ids"].append(a["id"])
                store.save(a["id"], "attempt", a)
    store.save(identity, "run", run)
    queue = Queue("codeproof", connection=redis)
    for attempt_id in run["attempt_ids"]:
        queue.enqueue(
            "app.worker.execute",
            attempt_id,
            job_id=attempt_id,
            job_timeout=body.budget.seconds + 150,
            result_ttl=3600,
        )
    return detail(run)


@app.get("/api/runs/{identity}")
def run(identity: str):
    return detail(require(identity, "run"))


@app.get("/api/attempts/{identity}")
def attempt(identity: str):
    return require(identity, "attempt")


@app.get("/api/attempts/{identity}/artifacts/{name}")
def artifact(identity: str, name: str):
    value = require(identity, "attempt")
    if name not in ("diff", "events") or name not in value:
        raise HTTPException(404, "Artifact not found")
    content = value[name] if name == "diff" else json.dumps(value[name], indent=2)
    return Response(
        content,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{identity}-{name}.txt"'},
    )


@app.post("/api/runs/{identity}/cancel")
def cancel(identity: str):
    value = require(identity, "run")
    value["cancelled"] = True
    store.save(identity, "run", value)
    for aid in value["attempt_ids"]:
        a = store.get(aid)
        if a["status"] == "Queued":
            a["status"] = "Cancelled"
            store.save(aid, "attempt", a)
    return detail(value)


@app.get("/api/runs/{identity}/events")
async def events(identity: str, request: Request):
    require(identity, "run")

    async def generate():
        previous = None
        while not await request.is_disconnected():
            value = run(identity)
            encoded = json.dumps(value)
            if encoded != previous:
                yield f"id: {time.time_ns()}\nevent: snapshot\ndata: {encoded}\n\n"
                previous = encoded
            else:
                yield ": heartbeat\n\n"
            if all(
                a["status"] in {"Completed", "Failed", "Timed Out", "Cancelled"}
                for a in value["attempts"]
            ):
                break
            await asyncio.sleep(1)

    return StreamingResponse(
        generate(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"}
    )


@app.get("/api/compare")
def compare():
    values = runs()
    return {
        "groups": {mode: [r for r in values if r["mode"] == mode] for mode in ("demo", "live")},
        "warning": "Compare only matching task versions, models and equal budgets. Repetitions are not pass@k.",
    }


@app.get("/api/runs/{identity}/report/{format}")
def report(identity: str, format: str):
    value = run(identity)
    value["methodology"] = (
        "Strict success: all trusted public, hidden and regression tests pass within budgets. Infrastructure failures excluded from valid denominator. Demo replay is not model performance. Missing usage and pricing are null."
    )
    if format == "json":
        content, media = json.dumps(value, indent=2), "application/json"
    elif format == "csv":
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(
            [
                "attempt",
                "mode",
                "task",
                "version",
                "strategy",
                "status",
                "success",
                "tokens",
                "cost",
            ]
        )
        for a in value["attempts"]:
            writer.writerow(
                [
                    a["id"],
                    a["mode"],
                    a["task_id"],
                    a["task_version"],
                    a["strategy"],
                    a["status"],
                    (a.get("evaluation") or {}).get("success"),
                    a["tokens"],
                    a["cost"],
                ]
            )
        content, media = out.getvalue(), "text/csv"
    elif format == "html":
        content = (
            '<!doctype html><html lang="en"><meta charset="utf-8"><title>CodeProof report</title><h1>'
            + html.escape(value["title"])
            + "</h1><p>"
            + html.escape(value["mode"])
            + "</p><pre>"
            + html.escape(json.dumps(value, indent=2))
            + "</pre></html>"
        )
        media = "text/html"
    else:
        raise HTTPException(404, "Unknown format")
    return Response(
        content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="codeproof-{identity}.{format}"'},
    )


class SettingsBody(Strict):
    worker_concurrency: int = Field(ge=1, le=4)


@app.get("/api/settings")
def settings():
    return store.get("local-settings") or {"worker_concurrency": 1}


@app.post("/api/settings")
def update_settings(body: SettingsBody):
    value = body.model_dump()
    store.save("local-settings", "settings", value)
    return value
