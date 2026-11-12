"""Run every check, preserve evidence, and fail when required checks are blocked."""

import hashlib
import os
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
evidence = ROOT / ".local/verification"
evidence.mkdir(parents=True, exist_ok=True)
project = "codeproof-verify-" + uuid.uuid4().hex[:10]
compose = ["docker", "compose", "-p", project, "-f", "docker-compose.verify.yml"]
checks = [
    ("Disposable verification infrastructure", compose + ["up", "-d", "--wait"]),
    (
        "Offline task image",
        ["docker", "build", "-f", "Dockerfile.task", "-t", "codeproof-task:1", "."],
    ),
    ("Python lint", [".venv/bin/ruff", "check", "backend", "scripts"]),
    ("Python formatting", [".venv/bin/ruff", "format", "--check", "backend", "scripts"]),
    ("Frontend lint", ["npm", "run", "lint", "--prefix", "frontend"]),
    ("Frontend formatting", ["npm", "run", "format:check", "--prefix", "frontend"]),
    ("Backend and migration tests", [".venv/bin/pytest", "-q", "-m", "not docker"]),
    ("Frontend production build and TypeScript", ["npm", "run", "build", "--prefix", "frontend"]),
    (
        "Source security scan (medium+ gate; low findings reviewed in SECURITY.md)",
        [".venv/bin/bandit", "-r", "backend/app", "scripts", "-ll"],
    ),
    ("Dependency scan Python", [".venv/bin/pip-audit", "-r", "requirements.lock"]),
    ("Dependency scan npm", ["npm", "audit", "--prefix", "frontend", "--audit-level=low"]),
    ("Secret and history scan", [".venv/bin/python", "scripts/scan_secrets.py"]),
    (
        "Browser exploration and offline states",
        ["npm", "run", "test:e2e", "--prefix", "frontend", "--", "--grep", "exploration"],
    ),
    ("Docker fixtures and isolation", [".venv/bin/pytest", "-q", "-m", "docker"]),
    (
        "Full browser benchmark workflow",
        ["npm", "run", "test:e2e", "--prefix", "frontend", "--", "--grep", "real evaluator"],
    ),
]
results = []
for index, (label, command) in enumerate(checks):
    print(f"[{index + 1}/{len(checks)}] {label}", flush=True)
    if label.startswith(
        ("Docker", "Full browser", "Disposable", "Offline task")
    ) and not shutil.which("docker"):
        results.append((label, "BLOCKED", "Docker unavailable; required check cannot run."))
        continue
    env = os.environ.copy()
    env["PYTHONPATH"] = "backend"
    if label.startswith("Full browser"):
        env["CODEPROOF_FULL_E2E"] = "1"
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, env=env, timeout=600, check=False
        )
        output = result.stdout + result.stderr
        status = "PASS" if result.returncode == 0 else "FAIL"
        if label.startswith("Disposable") and status == "PASS":

            def mapped_port(service, port):
                value = subprocess.run(
                    compose + ["port", service, str(port)],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                return int(value.rsplit(":", 1)[1])

            os.environ["TEST_POSTGRES_URL"] = (
                f"postgresql+psycopg://codeproof:codeproof-test-only@127.0.0.1:{mapped_port('db', 5432)}/verification"  # pragma: allowlist secret
            )
            os.environ["CODEPROOF_E2E_REDIS_URL"] = (
                f"redis://127.0.0.1:{mapped_port('redis', 6379)}/14"
            )
    except (OSError, subprocess.TimeoutExpired) as error:
        status, output = "BLOCKED", str(error)
    (evidence / f"{index + 1:02d}.log").write_text(output)
    output = output.replace(str(ROOT), "[workspace]").replace(str(Path.home()), "[home]")
    results.append((label, status, output[-2000:]))
    print(status, flush=True)
# Tree digest avoids claiming a tested commit when report generation changes files.
tracked = sorted(
    p
    for p in ROOT.rglob("*")
    if p.is_file()
    and not any(
        part
        in {
            ".venv",
            "node_modules",
            ".git",
            ".local",
            "artifacts",
            "dist",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
            "test-results",
            "playwright-report",
        }
        for part in p.relative_to(ROOT).parts
    )
    and p.name != "FINAL_TEST_REPORT.md"
    and p.suffix not in (".db", ".tsbuildinfo")
)
digest = hashlib.sha256()
for path in tracked:
    digest.update(str(path.relative_to(ROOT)).encode())
    digest.update(path.read_bytes())
revision = (
    subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    or "No commit yet"
)
lines = [
    "# Final test report",
    "",
    f"Generated: {datetime.now(UTC).isoformat()}",
    f"Base revision: {revision}; uncommitted source may be included.",
    f"Tested source-tree SHA256 (excluding this report and ignored runtime output): `{digest.hexdigest()}`",
    "",
    "This is execution evidence, not a completion certificate. BLOCKED required checks make `make verify` fail.",
    "",
    "| Check | Result |",
    "|---|---|",
]
lines += [f"| {label} | {status} |" for label, status, _ in results]
lines += ["", "## Commands and execution evidence", ""]
for (label, command), (_, status, output) in zip(checks, results):
    lines += [
        f"### {label}: {status}",
        "",
        "`" + " ".join(command) + "`",
        "",
        "```text",
        output.replace("```", "---"),
        "```",
        "",
    ]
lines += [
    "## Security findings and fixes",
    "",
    "Initial npm findings were resolved by upgrading Vite/PostCSS and overriding vulnerable minimatch. Unsafe fixed runner temporary names were replaced with OS-generated names. The one B108 annotation covers a container-private tmpfs mount; source scan low subprocess findings are reviewed in SECURITY.md, not evidence of zero risk. History is scanned as whole files to preserve scanner context; no existing history was rewritten. Live credential/spending checks were not bypassed.",
    "",
    "## Limitations and skipped checks",
    "",
    "Live gateway calls: not run; no credentials and no authorized spending amount. No demo result substitutes for live integration.",
    "Docker-dependent execution, cancellation, recovery and evaluator browser flow must pass on a Docker-equipped host. Read SECURITY.md for reviewed source scan findings and the local-only threat model.",
    "GitHub upload/CI status is separate from these local checks. No public deployment is claimed.",
    "",
    "## Reproduce",
    "",
    "`make setup && make verify` on a Docker-equipped machine. Logs are local-only under `.local/verification/`. No user database is reset by verification.",
]
(ROOT / "FINAL_TEST_REPORT.md").write_text("\n".join(lines) + "\n")
if shutil.which("docker"):
    subprocess.run(compose + ["down", "-v"], capture_output=True, check=False)
sys.exit(any(status != "PASS" for _, status, _ in results))
