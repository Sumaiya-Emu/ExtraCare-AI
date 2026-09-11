"""Locate the latest ExtraCare AI synthetic submission traces and optionally share them.

Run this after ``python scripts/validate_live.py``. By default the command is read-only. Passing
``--share`` explicitly creates public LangSmith links; use only after confirming that the selected
traces contain the bundled synthetic demo data and no private patient information.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.config import settings

TRACE_LABELS = {
    "lab": "LangSmith Lab Decoder trace",
    "product": "LangSmith Product Sentinel trace with live search",
    "cross_match": "LangSmith Cross-Match trace",
}


def _usable_configuration() -> bool:
    tracing_on = os.getenv(
        "LANGSMITH_TRACING", os.getenv("LANGCHAIN_TRACING_V2", "false")
    ).strip().casefold() in {"1", "true", "yes", "on"}
    return settings.has_langsmith_api_key() and tracing_on


def _mode_from_run(run: Any) -> str | None:
    inputs = getattr(run, "inputs", None) or {}
    if isinstance(inputs, dict):
        mode = inputs.get("mode")
        if mode in TRACE_LABELS:
            return mode
    metadata = (getattr(run, "extra", None) or {}).get("metadata", {})
    if isinstance(metadata, dict):
        mode = metadata.get("mode")
        if mode in TRACE_LABELS:
            return mode
    return None


def _runs_from_live_results(client: Any) -> dict[str, Any]:
    path = ROOT / "docs" / "audit_evidence" / "live_results.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        ids = payload.get("trace_run_ids", {})
        wanted = [ids[m] for m in TRACE_LABELS if ids.get(m)]
        if not wanted:
            return {}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            runs = list(client.list_runs(run_ids=wanted, limit=len(wanted)))
        by_id = {str(run.id): run for run in runs}
        return {mode: by_id[str(ids[mode])] for mode in TRACE_LABELS if str(ids.get(mode)) in by_id}
    except Exception:
        return {}


def _latest_mode_runs(client: Any, project: str, since_minutes: int) -> dict[str, Any]:
    selected = _runs_from_live_results(client)
    if len(selected) == len(TRACE_LABELS):
        return selected

    start = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        runs = list(
            client.list_runs(
                project_name=project,
                is_root=True,
                start_time=start,
                limit=80,
            )
        )
    runs.sort(key=lambda run: getattr(run, "start_time", start), reverse=True)
    for run in runs:
        mode = _mode_from_run(run)
        if mode and mode not in selected:
            selected[mode] = run
    return selected


def _share_run(client: Any, run: Any) -> str:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        existing = client.read_run_shared_link(run.id)
        return existing or client.share_run(run.id)


def _update_submission_links(links: dict[str, str]) -> None:
    path = ROOT / "SUBMISSION_LINKS.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    updated = []
    seen: set[str] = set()
    for line in lines:
        replaced = False
        for mode, label in TRACE_LABELS.items():
            if line.startswith(f"| {label} |") and mode in links:
                updated.append(f"| {label} | {links[mode]} |")
                seen.add(mode)
                replaced = True
                break
        if not replaced:
            updated.append(line)
    missing_rows = [TRACE_LABELS[m] for m in links if m not in seen]
    if missing_rows:
        raise RuntimeError("Could not find SUBMISSION_LINKS.md row(s): " + ", ".join(missing_rows))
    path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--since-minutes",
        type=int,
        default=180,
        help="Fallback look-back window when live_results.json does not contain usable run IDs.",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Intentionally create public share links for the selected synthetic traces.",
    )
    parser.add_argument(
        "--update-submission-links",
        action="store_true",
        help="Write created share links into SUBMISSION_LINKS.md (requires --share).",
    )
    args = parser.parse_args()

    if args.update_submission_links and not args.share:
        print("ERROR: --update-submission-links requires --share.")
        return 2
    if not _usable_configuration():
        print(
            "ERROR: configure a real LangSmith key and enable LANGSMITH_TRACING=true, "
            "then restart the shell/app."
        )
        return 2

    from langsmith import Client

    project = os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT", "ExtraCare-AI")
    client = Client()
    selected = _latest_mode_runs(client, project, max(args.since_minutes, 1))

    missing = [mode for mode in TRACE_LABELS if mode not in selected]
    if missing:
        print("Missing recent synthetic root trace(s): " + ", ".join(missing))
        print("Run: python scripts/validate_live.py")
        print("Then rerun this command shortly afterward.")
        return 1

    print(f"Found candidate traces in project {project!r}:")
    for mode in TRACE_LABELS:
        run = selected[mode]
        print(f"  {mode:12s} {run.id}  {getattr(run, 'start_time', '')}")

    if not args.share:
        print("\nRead-only mode: no trace was made public.")
        print("Inspect these runs in LangSmith. If they contain synthetic data only, rerun with --share.")
        return 0

    links = {mode: _share_run(client, selected[mode]) for mode in TRACE_LABELS}
    evidence = {
        "project": project,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Public links created intentionally from synthetic submission-validation traces.",
        "traces": {
            mode: {"run_id": str(selected[mode].id), "share_url": links[mode]}
            for mode in TRACE_LABELS
        },
    }
    destination = ROOT / "docs" / "audit_evidence" / "langsmith_trace_links.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    if args.update_submission_links:
        _update_submission_links(links)

    print(f"\nCreated share links and wrote {destination.relative_to(ROOT)}")
    if args.update_submission_links:
        print("Updated the LangSmith rows in SUBMISSION_LINKS.md")
    print("Open every link in a private/incognito browser before submitting it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
