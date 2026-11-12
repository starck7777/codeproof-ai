"""Trusted parent grades JSON results; candidate cannot author grading reports.
Tests are only mounted in this phase, never in the agent's workspace.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

work = Path(tempfile.mkdtemp(prefix="codeproof-work-"))
work.chmod(0o755)
shutil.copy("/candidate/solution.py", work / "solution.py")
cases = json.loads(Path("/trusted/cases.json").read_text())
# Each invocation gets an input, never an expected value. Keep one child for all
# cases to expose mutable default state. Parent compares after child exits.
child = """
import json, sys
from solution import solve
values = []
for args in json.loads(sys.stdin.read()):
    try:
        values.append({"value": solve(*args)})
    except Exception as error:
        values.append({"exception": type(error).__name__})
print(json.dumps(values))
"""
# Bounded file output avoids unbounded capture_output memory growth.
with tempfile.TemporaryFile() as output:
    process = subprocess.Popen(
        ["python", "-c", child],
        cwd=work,
        stdin=subprocess.PIPE,
        stdout=output,
        stderr=subprocess.DEVNULL,
        env={"PATH": os.environ["PATH"], "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(work)},
    )
    try:
        process.communicate(json.dumps([args for args, _ in cases]).encode(), timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    output.seek(0)
    try:
        values = json.loads(output.read(65536))
        if process.returncode != 0 or not isinstance(values, list) or len(values) != len(cases):
            values = []
    except (ValueError, UnicodeDecodeError):
        values = []
passed = 0
for item, (_, expected) in zip(values, cases):
    target = {"exception": "ValueError"} if expected == "ValueError" else {"value": expected}
    passed += item == target
print(json.dumps({"passed": passed, "total": len(cases)}))
