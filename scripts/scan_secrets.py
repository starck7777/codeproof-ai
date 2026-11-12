"""Scan publishable source plus each existing Git revision without printing secrets."""

import json
import subprocess
import sys
from pathlib import Path

from detect_secrets import SecretsCollection
from detect_secrets.settings import default_settings

root = Path.cwd()
ignored = {
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
findings = []
with default_settings():
    collection = SecretsCollection()
    for path in root.rglob("*"):
        if (
            not path.is_file()
            or any(p in ignored for p in path.relative_to(root).parts)
            or path.suffix == ".db"
            or path.name == ".env"
        ):
            continue
        collection.scan_file(str(path))
    findings.extend(collection.json().keys())
    revisions = subprocess.run(
        ["git", "rev-list", "--all"], capture_output=True, text=True, check=False
    )
    # Scan text from every historical commit, not just HEAD; no history rewriting.
    for revision in revisions.stdout.splitlines():
        tree = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", revision],
            capture_output=True,
            text=True,
            check=True,
        )
        for name in tree.stdout.splitlines():
            content = subprocess.run(
                ["git", "show", revision + ":" + name], capture_output=True, text=True, check=True
            ).stdout
            from detect_secrets.core.scan import scan_line

            for n, line in enumerate(content.splitlines(), 1):
                if list(scan_line(line)):
                    findings.append(f"history:{revision[:8]}:{name}:{n}")
if findings:
    print(json.dumps({"finding_locations": sorted(set(findings))}, indent=2))
    sys.exit(1)
print(
    "No candidate secrets detected in publishable source or existing Git history; this is not a guarantee."
)
