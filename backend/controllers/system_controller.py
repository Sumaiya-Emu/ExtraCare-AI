"""System/file controllers used by the frontend without exposing backend internals."""
from __future__ import annotations

from pathlib import Path

from backend.config import settings
from backend.tools.pdf_utils import ensure_image_bytes


def load_sample_asset(filename: str) -> bytes:
    path = (settings.SAMPLE_IMAGES_DIR / Path(filename).name).resolve()
    root = settings.SAMPLE_IMAGES_DIR.resolve()
    if root not in path.parents:
        raise ValueError("Invalid sample asset path.")
    return path.read_bytes()


def preview_document(data: bytes) -> bytes:
    return ensure_image_bytes(data)


def startup_status() -> dict[str, object]:
    """Return a non-secret environment readiness summary for the UI/preflight script."""
    return {
        "groq": settings.has_groq_api_key(),
        "tavily": settings.has_tavily_api_key(),
        "langsmith": settings.has_langsmith_api_key(),
        "missing_required": settings.missing_required_keys(),
        "chat_model": settings.CHAT_MODEL_NAME,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "default_analysis_mode": settings.DEFAULT_ANALYSIS_MODE,
    }
