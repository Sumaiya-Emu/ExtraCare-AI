"""Central configuration: environment variables, model names, and LangSmith setup."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def _usable_secret(value: str | None) -> bool:
    """Reject empty values and common ``.env.example`` placeholders."""
    clean = (value or "").strip().strip('"').strip("'")
    if not clean:
        return False
    lowered = clean.casefold()
    placeholder_markers = (
        "your-",
        "your_",
        "replace-me",
        "replace_me",
        "changeme",
        "example-key",
        "api-key-here",
        "insert-key",
    )
    return not any(marker in lowered for marker in placeholder_markers)


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY", "")
# Backward-compatible name used by older project code/tests.
LANGCHAIN_API_KEY = LANGSMITH_API_KEY

CHAT_MODEL_NAME = os.getenv("CHAT_MODEL_NAME", "qwen/qwen3.6-27b")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "qwen/qwen3.6-27b")
# Chroma's bundled local DefaultEmbeddingFunction uses all-MiniLM-L6-v2.
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "900"))
GROQ_TIMEOUT_SECONDS = int(os.getenv("GROQ_TIMEOUT_SECONDS", "60"))
GROQ_REASONING_FORMAT = os.getenv("GROQ_REASONING_FORMAT", "hidden").strip().lower()
GROQ_REASONING_EFFORT = os.getenv("GROQ_REASONING_EFFORT", "none").strip().lower()
# qwen/qwen3.6-27b currently accepts up to 3 input images per request.
MAX_PDF_PAGES = min(3, max(1, int(os.getenv("MAX_PDF_PAGES", "3"))))
DEFAULT_ANALYSIS_MODE = os.getenv("DEFAULT_ANALYSIS_MODE", "fast").strip().lower()

KNOWLEDGE_BASE_DIR = BASE_DIR / "data" / "knowledge_base"
SAMPLE_IMAGES_DIR = BASE_DIR / "data" / "sample_images"
VECTOR_STORE_DIR = BASE_DIR / "data" / "vector_store"

CLINICAL_COLLECTION = "clinical_guidelines"
TOXICOLOGY_COLLECTION = "toxicology_standards"

SAFE_THRESHOLD = 75
CAUTION_THRESHOLD = 40

RISK_TONES = {
    "Safe": "safe",
    "Caution": "caution",
    "Toxic": "danger",
}


def has_groq_api_key() -> bool:
    return _usable_secret(GROQ_API_KEY)


def has_tavily_api_key() -> bool:
    return _usable_secret(TAVILY_API_KEY)


def has_langsmith_api_key() -> bool:
    return _usable_secret(LANGSMITH_API_KEY)


def tracing_requested() -> bool:
    raw = os.getenv("LANGSMITH_TRACING", os.getenv("LANGCHAIN_TRACING_V2", "false"))
    return raw.strip().casefold() in {"1", "true", "yes", "on"}


def configure_langsmith() -> None:
    """Normalize modern and legacy LangSmith environment aliases.

    Tracing is enabled only when the user explicitly requests it *and* a non-placeholder key is
    configured.  This keeps normal local use quiet while making the final demo configuration
    compatible with both current ``LANGSMITH_*`` names and older ``LANGCHAIN_*`` aliases.
    """
    enabled = tracing_requested() and has_langsmith_api_key()
    endpoint = os.getenv("LANGSMITH_ENDPOINT") or os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    project = os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT", "ExtraCare-AI")

    os.environ["LANGSMITH_TRACING"] = "true" if enabled else "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if enabled else "false"
    os.environ["LANGSMITH_ENDPOINT"] = endpoint
    os.environ["LANGCHAIN_ENDPOINT"] = endpoint
    os.environ["LANGSMITH_PROJECT"] = project
    os.environ["LANGCHAIN_PROJECT"] = project

    if enabled:
        os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
        os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY


configure_langsmith()


def missing_required_keys() -> list[str]:
    missing = []
    if not has_groq_api_key():
        missing.append("GROQ_API_KEY")
    return missing
