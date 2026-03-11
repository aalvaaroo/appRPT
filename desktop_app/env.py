from __future__ import annotations

import os
from pathlib import Path


def _read_text(path: Path) -> str | None:
    for enc in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
        except OSError:
            return None
    return None


def load_dotenv(base_dir: Path) -> None:
    env_path = base_dir / ".env"
    if not env_path.exists():
        return
    content = _read_text(env_path)
    if not content:
        return
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
