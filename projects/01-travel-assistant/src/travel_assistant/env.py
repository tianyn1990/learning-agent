from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def load_env_file(path: Optional[str] = None) -> None:
    """
    Minimal `.env` loader (no extra dependency).

    - Ignores blank lines and `#` comments
    - Supports `KEY=VALUE` with optional surrounding quotes
    - Does not override existing environment variables
    """
    env_path = Path(path) if path else Path.cwd() / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if not key or key in os.environ:
            continue
        os.environ[key] = value

