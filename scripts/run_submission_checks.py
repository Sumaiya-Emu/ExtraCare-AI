"""Run all non-network submission checks in one command."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

raise SystemExit(
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "preflight.py"), "--submission"],
        cwd=ROOT,
        check=False,
    ).returncode
)
