"""Start the full local stack, wait for readiness, retain only owned processes."""

import os
import signal
import socket
import subprocess
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
processes = []
logs = []
for port in (8000, 5173):
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", port)) == 0:
            raise SystemExit(
                f"Port {port} is occupied. No process was stopped. Configure alternate ports before starting."
            )
try:
    subprocess.run(
        ["docker", "build", "-f", "Dockerfile.task", "-t", "codeproof-task:1", "."], check=True
    )
    (ROOT / "artifacts").mkdir(exist_ok=True)
    os.environ["LOCAL_UID"] = str(os.getuid())
    os.environ["LOCAL_GID"] = str(os.getgid())
    subprocess.run(["docker", "compose", "up", "-d", "--build"], check=True)
    local = ROOT / ".local"
    local.mkdir(exist_ok=True)
    env = (
        os.environ
        | {
            "PYTHONPATH": "backend",
            "DATABASE_URL": "postgresql+psycopg://codeproof:codeproof-local-demo@127.0.0.1/codeproof",  # pragma: allowlist secret
            "REDIS_URL": "redis://127.0.0.1:6379/0",
        }
    )  # pragma: allowlist secret - public local demo URL
    for name, command, environment in [
        ("worker", [".venv/bin/python", "-m", "app.worker"], env),
        (
            "frontend",
            ["npm", "run", "dev", "--prefix", "frontend", "--", "--port", "5173", "--strictPort"],
            os.environ.copy(),
        ),
    ]:
        log = open(local / (name + ".log"), "a")
        logs.append(log)
        processes.append(
            subprocess.Popen(command, env=environment, stdout=log, stderr=subprocess.STDOUT)
        )
    (local / "stack.pid").write_text(str(os.getpid()))

    def stop(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    deadline = time.monotonic() + 90
    with httpx.Client(trust_env=False) as client:
        while time.monotonic() < deadline:
            if any(p.poll() is not None for p in processes):
                raise RuntimeError("A service exited; inspect .local logs")
            try:
                ready = client.get("http://127.0.0.1:8000/api/health").json()
                frontend = client.get("http://127.0.0.1:5173/").is_success
                if all(ready.get(k) for k in ("database", "redis", "worker_ready")) and frontend:
                    break
            except (httpx.HTTPError, ValueError):
                pass
            time.sleep(1)
        else:
            raise RuntimeError("Readiness timeout; inspect docker compose logs and .local logs")
    print("READY http://127.0.0.1:5173 — stop with make stop-all", flush=True)
    workers = [processes[0]]
    frontend_process = processes[1]
    with httpx.Client(trust_env=False) as client:
        while frontend_process.poll() is None:
            desired = client.get("http://127.0.0.1:8000/api/settings").json()["worker_concurrency"]
            while len(workers) < desired:
                worker = subprocess.Popen(
                    [".venv/bin/python", "-m", "app.worker"],
                    env=env,
                    stdout=logs[0],
                    stderr=subprocess.STDOUT,
                )
                workers.append(worker)
                processes.append(worker)
            while len(workers) > desired:
                worker = workers.pop()
                worker.terminate()  # RQ warm shutdown: finish the current job first.
            if any(worker.poll() is not None for worker in workers):
                raise RuntimeError("A worker exited; inspect .local/worker.log")
            time.sleep(2)
finally:
    for p in processes:
        if p.poll() is None:
            p.terminate()
    for p in processes:
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
    for log in logs:
        log.close()
    (ROOT / ".local/stack.pid").unlink(missing_ok=True)
    subprocess.run(["docker", "compose", "down"], check=False)
