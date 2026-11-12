"""Run local read-only exploration or host-worker development; owns only its children."""

import os
import signal
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.chdir(root)
processes = []
try:
    subprocess.run(
        [".venv/bin/python", "-m", "app.seed"],
        env=os.environ | {"PYTHONPATH": "backend"},
        check=True,
    )
    processes.append(
        subprocess.Popen(
            [".venv/bin/uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            env=os.environ | {"PYTHONPATH": "backend"},
        )
    )
    processes.append(
        subprocess.Popen(
            ["npm", "run", "dev", "--prefix", "frontend", "--", "--port", "5173", "--strictPort"]
        )
    )
    Path(".local").mkdir(exist_ok=True)
    Path(".local/dev.pid").write_text(str(os.getpid()))
    print("Local application: http://127.0.0.1:5173 ; stop with make stop", flush=True)

    def stop(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    while all(p.poll() is None for p in processes):
        time.sleep(0.5)
finally:
    for p in processes:
        if p.poll() is None:
            p.terminate()
    for p in processes:
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
    Path(".local/dev.pid").unlink(missing_ok=True)
