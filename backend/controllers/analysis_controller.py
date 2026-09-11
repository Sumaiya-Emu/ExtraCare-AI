"""Application controllers.

The frontend calls only these orchestration functions. Agents, RAG, external APIs, and
clinical algorithms remain behind this boundary.
"""
from __future__ import annotations

import logging
from typing import Optional

import groq

logger = logging.getLogger(__name__)

from backend.agents.disease_hub_agent import generate_disease_protocol
from backend.config import settings
from backend.core.care_delta import compare_lab_results
from backend.core.care_graph import build_care_graph, care_graph_to_dot
from backend.core.disease_protocol_local import generate_local_disease_protocol
from backend.core.doctor_brief import build_doctor_brief
from backend.models.schemas import (
    CareDelta,
    DiseaseProtocol,
    ExtractedLabData,
    AnalysisConfidence,
    PatientProfile,
    PipelineOutput,
    RiskReport,
)
from backend.rag.vector_store import ingest_knowledge_base
from backend.workflow.graph import run_pipeline


def ensure_knowledge_base_ready() -> bool:
    """Build the persistent local Chroma collections using local embeddings."""
    ingest_knowledge_base()
    return True


def _analysis_failure_reason(exc: Exception) -> str:
    """Translate a raw provider exception into an actionable, non-technical reason."""
    if isinstance(exc, groq.RateLimitError):
        return "Groq's usage limit for this minute was reached. Wait about a minute, then click Analyze again."
    if isinstance(exc, groq.AuthenticationError):
        return "The configured GROQ_API_KEY was rejected. Check the key in your .env file."
    if isinstance(exc, (groq.APIConnectionError, groq.APITimeoutError)):
        return "Could not reach the Groq service (network or timeout). Check your internet connection and retry."
    if isinstance(exc, groq.BadRequestError):
        return "Groq rejected this request (for example, the document/image may be too large). Try a smaller or clearer file."
    if isinstance(exc, (ImportError, OSError)) and "onnxruntime" in str(exc).lower():
        return (
            "The local embedding model (onnxruntime) failed to load on this machine, so the "
            "evidence lookup step could not run. Reinstall the Microsoft Visual C++ Redistributable "
            "and onnxruntime, or retry with a Python 3.12 environment."
        )
    return "The analysis service encountered an unexpected infrastructure error. Please retry."


def analyze(
    mode: str,
    profile: PatientProfile,
    *,
    image_bytes: Optional[bytes] = None,
    product_image_bytes: Optional[bytes] = None,
    ingredients_text: Optional[str] = None,
    fast_mode: bool = False,
    expected_product_type: Optional[str] = None,
) -> PipelineOutput:
    """Execute a typed analysis workflow through the backend graph."""
    try:
        return run_pipeline(
            mode=mode,
            profile=profile,
            image_bytes=image_bytes,
            product_image_bytes=product_image_bytes,
            ingredients_text=ingredients_text,
            fast_mode=fast_mode,
            expected_product_type=expected_product_type,
        )
    except Exception as exc:
        # Controller boundary: network/library failures must become a fail-closed typed response,
        # not a Streamlit traceback or a false low-risk verdict. The real exception is logged to
        # the console (never shown in the UI) so the actual cause can still be diagnosed.
        logger.exception("analyze() failed for mode=%s", mode)
        return PipelineOutput(
            mode=mode,
            status="unable_to_assess",
            confidence=AnalysisConfidence(
                level="low",
                score=0,
                reasons=[_analysis_failure_reason(exc)],
                can_show_verdict=False,
            ),
            warnings=["No clinical conclusion was published because the analysis did not complete reliably."],
        )


def generate_protocol(disease_name: str, *, fast_mode: bool) -> DiseaseProtocol:
    """Generate a disease protocol with graceful local fallback."""
    normalized = disease_name.strip()
    if not normalized:
        return generate_local_disease_protocol("")

    if fast_mode or not settings.has_groq_api_key():
        return generate_local_disease_protocol(normalized)

    try:
        ensure_knowledge_base_ready()
        return generate_disease_protocol(normalized, use_live_search=True)
    except Exception:
        # The Disease Hub is educational. Infrastructure failure must not crash the app or
        # silently manufacture a live answer; use the bundled conservative evidence fallback.
        logger.exception("generate_protocol() failed for disease_name=%s", normalized)
        return generate_local_disease_protocol(normalized)


def build_delta(previous: ExtractedLabData, current: ExtractedLabData) -> CareDelta:
    return compare_lab_results(previous, current)


def build_care_graph_dot(profile: PatientProfile, report: RiskReport) -> str:
    return care_graph_to_dot(build_care_graph(profile, report))


def build_visit_brief(
    profile: PatientProfile,
    output: PipelineOutput,
    delta: CareDelta | None = None,
) -> str:
    return build_doctor_brief(profile, output, delta)
