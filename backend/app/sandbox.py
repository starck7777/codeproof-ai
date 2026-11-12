"""Only trusted worker imports this module. No host execution fallback."""

import json
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

IMAGE = "codeproof-task:1"
# Container-private bounded tmpfs, never a shared host temporary path.
CONTAINER_TMPFS = "/tmp:rw,noexec,nosuid,size=32m,mode=1777"  # nosec B108


class Sandbox:
    def __init__(self, cancelled=lambda: False, deadline=None):
        self.cancelled = cancelled
        self.deadline = deadline or time.monotonic() + 120
        self.active = None

    def run(self, workspace, tests, seconds=15):
        if not shutil.which("docker"):
            raise RuntimeError("Docker unavailable; isolated execution disabled")
        name = "codeproof-" + uuid.uuid4().hex
        self.active = name
        # Source is copied to tmpfs; candidate cannot alter trusted mounted tests.
        args = [
            "docker",
            "run",
            "--rm",
            "--name",
            name,
            "--network",
            "none",
            "--read-only",
            "--user",
            "65534:65534",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--memory=128m",
            "--memory-swap=128m",
            "--cpus=.5",
            "--pids-limit=32",
            "--ulimit",
            "nofile=64:64",
            "--log-driver=none",
            "--ulimit",
            "fsize=131072:131072",
            "--tmpfs",
            CONTAINER_TMPFS,
            "--mount",
            f"type=bind,src={Path(workspace).resolve()},dst=/candidate,readonly",
            "--mount",
            f"type=bind,src={Path(tests).resolve()},dst=/trusted,readonly",
            IMAGE,
        ]
        try:
            with tempfile.TemporaryFile() as output:
                process = subprocess.Popen(args, stdout=output, stderr=subprocess.STDOUT)
                end = min(self.deadline, time.monotonic() + seconds)
                try:
                    while process.poll() is None:
                        if self.cancelled():
                            raise InterruptedError("cancelled")
                        if time.monotonic() > end:
                            raise TimeoutError("sandbox wall-clock deadline")
                        if output.tell() > 65536:
                            raise RuntimeError("output limit exceeded")
                        time.sleep(0.1)
                    output.seek(0)
                    raw = output.read(65536).decode(errors="replace")
                    # Fixed runner produces only counts; hidden failures never return inputs.
                    try:
                        result = json.loads(raw.strip().splitlines()[-1])
                    except (ValueError, IndexError):
                        raise RuntimeError("sandbox runner failed") from None
                    if (
                        set(result) != {"passed", "total"}
                        or not 0 <= result["passed"] <= result["total"]
                    ):
                        raise RuntimeError("invalid evaluator result")
                    return result
                finally:
                    subprocess.run(
                        ["docker", "rm", "-f", name], capture_output=True, timeout=15, check=False
                    )
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=5)
        finally:
            self.active = None
