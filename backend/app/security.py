import os
import re
from pathlib import Path
from urllib.parse import urlsplit


def safe_path(root: Path, name: str):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise ValueError("invalid path")
    root = root.resolve()
    path = root / name
    if Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError("invalid path")
    if any(p.is_symlink() for p in [path, *path.parents] if p.is_relative_to(root)):
        raise ValueError("symlink forbidden")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("path escape")
    return path


def patch_source(root, path, content):
    if path != "solution.py" or not isinstance(content, str) or len(content.encode()) > 32768:
        raise ValueError("protected file or oversized patch")
    safe_path(root, path).write_text(content)


def redact(text):
    for name in ("BIFROST_API_KEY", "BIFROST_VIRTUAL_KEY", "BIFROST_AUTHORIZATION"):
        secret = os.getenv(name)
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return re.sub(
        r"(?i)(authorization|api[_-]?key|token)\s*[:=]\s*[^\s,]+", r"\1=[REDACTED]", text
    )[:16384]


def gateway_url():
    # Exact operator-controlled allowlist. UI and model cannot configure URLs.
    url = os.getenv("BIFROST_URL", "http://127.0.0.1:8080").rstrip("/")
    allowed = os.getenv("GATEWAY_ALLOWED_ORIGINS", "http://127.0.0.1:8080").split(",")
    parsed = urlsplit(url)
    if (
        url not in allowed
        or parsed.scheme not in ("http", "https")
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path
    ):
        raise ValueError("gateway origin not allowlisted")
    return url
