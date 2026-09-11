"""ExtraCare AI preflight checks.

No network/API request is made. Use ``--static`` after installing dependencies when API keys are unavailable. Use ``--submission`` on the final demo machine to
require the assignment-specific live-search and LangSmith credentials as well.
"""
from __future__ import annotations

import argparse
import compileall
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

REQUIRED_MODULES = {
    "streamlit": "streamlit",
    "dotenv": "python-dotenv",
    "pydantic": "pydantic",
    "pymupdf": "pymupdf",
    "langgraph": "langgraph",
    "langchain_core": "langchain-core",
    "langchain_groq": "langchain-groq",
    "langchain_chroma": "langchain-chroma",
    "langsmith": "langsmith",
    "chromadb": "chromadb",
    "graphviz": "graphviz",
    "PIL": "pillow",
    "pytest": "pytest",
    "socksio": "httpx[socks]",
}
SUBMISSION_MODULES = {"tavily": "tavily-python"}


def _usable_secret(value: str | None) -> bool:
    clean = (value or "").strip().strip('"').strip("'")
    if not clean:
        return False
    lowered = clean.casefold()
    return not any(
        marker in lowered
        for marker in (
            "your-",
            "your_",
            "replace-me",
            "replace_me",
            "changeme",
            "example-key",
            "api-key-here",
            "insert-key",
        )
    )


def _check_json_files() -> bool:
    paths = [
        ROOT / "data" / "knowledge_base" / "clinical_guidelines.json",
        ROOT / "data" / "knowledge_base" / "toxicology_standards.json",
        ROOT / "data" / "knowledge_base" / "source_registry.json",
    ]
    ok = True
    for path in paths:
        try:
            json.loads(path.read_text(encoding="utf-8"))
            print(f"[OK] JSON: {path.relative_to(ROOT)}")
        except Exception as exc:
            print(f"[FAIL] JSON: {path.relative_to(ROOT)} — {exc}")
            ok = False
    return ok


def _check_external_css_rule() -> bool:
    ok = True
    pattern = re.compile(r"<style\b|style\s*=", re.IGNORECASE)
    for py_file in (ROOT / "frontend").rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="ignore")
        if pattern.search(text):
            print(f"[FAIL] Inline CSS/style found in {py_file.relative_to(ROOT)}")
            ok = False
    if ok:
        print("[OK] Styling rule: frontend Python contains no inline <style> or style= attributes")
    return ok


def _check_secret_hygiene() -> bool:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8", errors="ignore")
    ok = ".env" in gitignore and "secrets.toml" in gitignore
    print("[OK] .env and Streamlit secrets are ignored" if ok else "[FAIL] secret files are not fully ignored")

    secret_pattern = re.compile(r"(?:AIza[\w-]{20,}|gsk_[A-Za-z0-9_-]{20,}|tvly-[\w-]{10,}|lsv2_[\w-]{10,}|sk-[A-Za-z0-9]{20,})")
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", "venv", ".venv", "__pycache__"} for part in path.parts):
            continue
        if path.name == ".env":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if secret_pattern.search(text):
            print(f"[FAIL] Possible credential pattern in {path.relative_to(ROOT)}")
            ok = False
    if ok:
        print("[OK] No obvious credential pattern found in repository files")
    return ok


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", action="store_true", help="Run the installed runtime checks without requiring API keys.")
    parser.add_argument("--submission", action="store_true", help="Require Tavily and LangSmith configuration for the final demo machine.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print("ExtraCare AI preflight\n")
    failures = 0

    if not ((3, 11) <= sys.version_info[:2] <= (3, 13)):
        print(f"[FAIL] Python {sys.version.split()[0]} — use Python 3.11–3.13 (3.12 recommended)")
        failures += 1
    else:
        print(f"[OK] Python {sys.version.split()[0]}")

    missing_packages: list[str] = []
    for module, package in REQUIRED_MODULES.items():
        present = importlib.util.find_spec(module) is not None
        print(f"[{'OK' if present else 'MISSING'}] {package}")
        if not present:
            missing_packages.append(package)

    tavily_present = importlib.util.find_spec("tavily") is not None
    print(f"[{'OK' if tavily_present else 'SUBMISSION'}] tavily-python")
    if args.submission and not tavily_present:
        failures += 1

    print("\nEnvironment")
    groq_ok = _usable_secret(os.getenv("GROQ_API_KEY"))
    tavily_ok = _usable_secret(os.getenv("TAVILY_API_KEY"))
    langsmith_ok = _usable_secret(os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY"))
    tracing_on = os.getenv("LANGSMITH_TRACING", os.getenv("LANGCHAIN_TRACING_V2", "false")).strip().casefold() in {"true", "1", "yes", "on"}
    if args.submission and not tracing_on:
        print("[FAIL] LangSmith tracing is disabled; enable LANGSMITH_TRACING=true (legacy LANGCHAIN_TRACING_V2=true also works).")
        failures += 1
    print("[OK] GROQ_API_KEY configured" if groq_ok else "[MISSING/PLACEHOLDER] GROQ_API_KEY — live AI analysis disabled")
    print("[OK] TAVILY_API_KEY configured" if tavily_ok else "[SUBMISSION] TAVILY_API_KEY absent — Fast mode still works, live-search demo does not")
    print("[OK] LangSmith API key configured" if langsmith_ok else "[SUBMISSION] LANGSMITH_API_KEY absent — tracing demo unavailable")

    if not args.static and (missing_packages or not groq_ok):
        failures += len(missing_packages) + (0 if groq_ok else 1)
    if args.submission and (not tavily_ok or not langsmith_ok):
        failures += (0 if tavily_ok else 1) + (0 if langsmith_ok else 1)

    print("\nStatic validation")
    if not compileall.compile_dir(ROOT, quiet=1, rx=re.compile(r"[\\/](?:venv|\.venv|__pycache__)[\\/]")):
        print("[FAIL] Python compilation")
        failures += 1
    else:
        print("[OK] Python compilation")
    failures += 0 if _check_json_files() else 1
    failures += 0 if _check_external_css_rule() else 1
    failures += 0 if _check_secret_hygiene() else 1

    print("\nRegression and offline integration tests")
    test = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, check=False)
    if test.returncode != 0:
        failures += 1

    if not missing_packages:
        try:
            sys.path.insert(0, str(ROOT))
            from backend.workflow.graph import build_graph

            build_graph()
            print("[OK] LangGraph compiled")
        except Exception as exc:
            print(f"[FAIL] LangGraph compile — {exc}")
            failures += 1
    else:
        print("[SKIP] LangGraph compile until runtime dependencies are installed")

    if failures:
        print(f"\nPreflight finished with {failures} blocking check(s).")
        return 1

    if args.static:
        print("\nStatic/package validation passed. Complete docs/LIVE_VALIDATION.md on the configured submission machine.")
    elif args.submission:
        print("\nSubmission preflight passed. Proceed with live workflow tests and capture LangSmith traces.")
    else:
        print("\nRuntime preflight passed. Use --submission before recording the final video/traces.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
