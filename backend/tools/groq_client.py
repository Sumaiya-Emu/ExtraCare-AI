"""Central Groq chat/vision client factory with stable JSON-oriented defaults."""
from __future__ import annotations

from langchain_groq import ChatGroq

from backend.config import settings
from backend.core.errors import AnalysisUnavailableError


def build_chat_model(
    *,
    vision: bool = False,
    reasoning_effort: str | None = None,
) -> ChatGroq:
    """Create the configured Groq chat or multimodal model.

    ExtraCare AI asks every cloud model call for JSON. Qwen 3.6 supports JSON mode,
    image input, and hidden reasoning on Groq. Hidden reasoning keeps ``<think>``
    blocks out of JSON while still allowing the model to reason when enabled.
    """
    if not settings.has_groq_api_key():
        raise AnalysisUnavailableError("GROQ_API_KEY is not configured.")

    model_name = settings.VISION_MODEL_NAME if vision else settings.CHAT_MODEL_NAME
    return ChatGroq(
        model=model_name,
        temperature=0,
        api_key=settings.GROQ_API_KEY,
        max_tokens=settings.MAX_OUTPUT_TOKENS,
        max_retries=2,
        timeout=settings.GROQ_TIMEOUT_SECONDS,
        reasoning_format=settings.GROQ_REASONING_FORMAT,
        reasoning_effort=reasoning_effort or settings.GROQ_REASONING_EFFORT,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
