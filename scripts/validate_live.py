"""Run synthetic-input cloud smoke tests and retain truthful output evidence.

Run only after configuring your own keys. Real API requests may incur provider charges.
This checks execution, not clinical validation or complete OCR accuracy.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.config import settings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "audit_evidence" / "live_results.json",
    )
    args = parser.parse_args()

    tracing_enabled = os.getenv(
        "LANGSMITH_TRACING", os.getenv("LANGCHAIN_TRACING_V2", "false")
    ).strip().casefold() in {"true", "1", "yes", "on"}
    required = {
        "Groq": settings.has_groq_api_key(),
        "Tavily": settings.has_tavily_api_key(),
        "LangSmith": settings.has_langsmith_api_key(),
        "Tracing enabled": tracing_enabled,
    }
    if not all(required.values()):
        print(
            "NOT RUN: configure "
            + ", ".join(k for k, v in required.items() if not v)
            + ". No live evidence was generated."
        )
        return 2

    from backend.controllers.analysis_controller import analyze, ensure_knowledge_base_ready
    from backend.core.tracing import traceable
    from backend.models.schemas import PatientProfile
    from backend.tools.search_tool import search_web
    from langsmith import Client
    from langsmith.run_helpers import tracing_context
from langchain_core.tracers.langchain import wait_for_all_tracers

    @traceable(
        "chain",
        name="submission_validation.workflow",
        tags=["submission", "synthetic-demo"],
    )
    def run_submission_mode(mode: str, profile: PatientProfile, lab: bytes, food: bytes):
        return analyze(
            mode,
            profile,
            image_bytes=food if mode == "product" else lab,
            product_image_bytes=food if mode == "cross_match" else None,
            expected_product_type="food" if mode == "cross_match" else None,
            fast_mode=False,
        )

    profile = PatientProfile(
        age=55,
        gender="Female",
        chronic_conditions=["Chronic Kidney Disease (CKD)"],
    )
    lab = (ROOT / "data/sample_images/sample_blood_test.png").read_bytes()
    food = (ROOT / "data/sample_images/sample_food_label.png").read_bytes()
    project = os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT", "ExtraCare-AI")
    results: dict[str, object] = {
        "validation_type": "LIVE API EXECUTION using bundled synthetic samples; inspect extracted text manually against the images",
        "project": project,
        "checks": {},
        "trace_run_ids": {},
    }

    try:
        client = Client()
        with tracing_context(
            enabled=True,
            project_name=project,
            tags=["submission", "synthetic-demo"],
            metadata={"dataset": "bundled synthetic samples"},
            client=client,
        ):
            ensure_knowledge_base_ready()
            results["checks"]["search"] = search_web(
                "FDA food recall safety alert", max_results=2
            )
            for mode in ("lab", "product", "cross_match"):
                run_id = uuid.uuid4()
                out = run_submission_mode(
                    mode,
                    profile,
                    lab,
                    food,
                    langsmith_extra={
                        "run_id": run_id,
                        "metadata": {"mode": mode, "synthetic_submission_validation": True},
                    },
                )
                results["checks"][mode] = out.model_dump()
                results["trace_run_ids"][mode] = str(run_id)
            wait_for_all_tracers()

        workflow_ok = all(
            results["checks"][mode]["status"] == "ok"
            for mode in ("lab", "product", "cross_match")
        )
        search_in_product_trace = bool(results["checks"]["product"].get("used_live_search"))
        results["product_trace_includes_live_search"] = search_in_product_trace
        results["status"] = "passed" if workflow_ok and search_in_product_trace else "failed"
        if not search_in_product_trace:
            results["failure_note"] = (
                "Product Sentinel completed but did not report live-search use. Verify that OCR extracted "
                "the synthetic product name and that Tavily search executed inside the Product workflow."
            )
        results["trace_note"] = (
            "The trace_run_ids identify the three synthetic submission-validation root traces. "
            "Open them in LangSmith, verify nested agent/tool/retrieval/LLM steps, then use "
            "scripts/export_langsmith_traces.py. Use --share only after confirming synthetic-only content."
        )
    except Exception as exc:
        results["status"] = "failed"
        results["error_type"] = type(exc).__name__
        results["error_message"] = str(exc)[:500]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print("Live execution:", results["status"], "â€” inspect", args.output)
    return 0 if results["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

