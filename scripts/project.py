"""Portable setup, validation, trace-export, and launch commands for the submission package."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
ENV_DIR = ROOT / ".venv"
PYTHON = ENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(*args: str) -> int:
    return subprocess.run(list(args), cwd=ROOT, check=False).returncode


def _print_install_diagnostics() -> None:
    """Give actionable help after a pip failure without pretending to know its cause."""
    try:
        socket.getaddrinfo("pypi.org", 443)
        print("PyPI DNS lookup: OK")
    except OSError:
        print("PyPI DNS lookup: FAILED")
        print("Your computer cannot currently resolve pypi.org. Check internet/DNS/VPN/proxy settings, then retry setup.")
        if os.name == "nt":
            print("Windows checks:  nslookup pypi.org   |   ipconfig /flushdns   |   Test-NetConnection pypi.org -Port 443")
        return
    print("Dependency installation still failed even though pypi.org resolves.")
    print("Retry the command and inspect the first pip ERROR above; a proxy/firewall or package download failure may be involved.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "run", "check", "live", "traces"])
    args = parser.parse_args()

    if args.command == "setup":
        if not (3, 11) <= sys.version_info[:2] <= (3, 13):
            print(f"Detected Python {sys.version.split()[0]}.")
            print("Install Python 3.11–3.13 (3.12 recommended), then run setup again.")
            return 1
        if not PYTHON.exists():
            print(f"Creating .venv with Python {sys.version.split()[0]}...", flush=True)
            try:
                venv.EnvBuilder(with_pip=True).create(ENV_DIR)
            except Exception as exc:
                print(f"Virtual environment creation failed ({type(exc).__name__}).")
                print("Ensure the Python venv/ensurepip component is installed and the project folder is writable.")
                return 1
        status = run(str(PYTHON), "-m", "pip", "install", "-r", "requirements.txt")
        if status:
            print("\nDependency installation failed.")
            _print_install_diagnostics()
            return status
        env_file = ROOT / ".env"
        if not env_file.exists():
            shutil.copyfile(ROOT / ".env.example", env_file)
            print("Created .env from .env.example (placeholders only).")
        else:
            print("Existing .env preserved.")
        print("Setup complete. Add your own keys to .env for live AI features.")
        return run(str(PYTHON), "scripts/preflight.py", "--static")

    if not PYTHON.exists():
        print("Run setup first: py scripts/project.py setup  (or: python scripts/project.py setup)")
        return 1

    if args.command == "run":
        return run(str(PYTHON), "-m", "streamlit", "run", "frontend/app.py")
    if args.command == "check":
        return run(str(PYTHON), "scripts/preflight.py", "--static")
    if args.command == "traces":
        return run(str(PYTHON), "scripts/export_langsmith_traces.py")

    status = run(str(PYTHON), "scripts/run_submission_checks.py")
    if status:
        return status
    return run(str(PYTHON), "scripts/validate_live.py")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Project command could not complete ({type(exc).__name__}). Check Python installation and folder permissions.")
        raise SystemExit(1)
