"""LangSmith tracing helpers with privacy-aware serialization.

The normal runtime uses the real :mod:`langsmith` ``traceable`` decorator.  A tiny no-op
fallback keeps pure-Python/core tests importable when the optional AI stack is not installed.

Public submission traces should use the bundled synthetic samples.  To reduce accidental leakage
and giant traces, this module summarizes binary payloads, redacts obvious credential/name fields,
and truncates very long strings before they are attached to our custom function spans.  Provider
SDK spans can still contain model prompts, so tracing remains disabled by default and should not be
enabled for real patient data.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from typing import Any

try:
    from langsmith import traceable as _langsmith_traceable  # type: ignore
except ImportError:  # pragma: no cover - minimal test environments only
    _langsmith_traceable = None

_REDACT_KEYS = {
    "api_key",
    "authorization",
    "password",
    "secret",
    "token",
    "patient_name",
}
_BINARY_KEYS = {
    "image_bytes",
    "product_image_bytes",
    "input_bytes",
    "file_bytes",
}
_MAX_TRACE_STRING = 4000
_MAX_TRACE_ITEMS = 50


def _safe_value(value: Any, *, key: str | None = None) -> Any:
    """Return a bounded, JSON-friendly representation suitable for traces."""
    normalized_key = (key or "").casefold()
    if any(marker in normalized_key for marker in _REDACT_KEYS):
        return "[REDACTED]"
    if isinstance(value, (bytes, bytearray, memoryview)):
        return {"binary_payload": True, "bytes": len(value)}
    if key in _BINARY_KEYS:
        try:
            return {"binary_payload": True, "bytes": len(value)}
        except TypeError:
            return "[BINARY INPUT]"
    if hasattr(value, "model_dump"):
        try:
            return _safe_value(value.model_dump())
        except Exception:
            return f"<{type(value).__name__}>"
    if isinstance(value, dict):
        items = list(value.items())[:_MAX_TRACE_ITEMS]
        cleaned = {str(k): _safe_value(v, key=str(k)) for k, v in items}
        if len(value) > _MAX_TRACE_ITEMS:
            cleaned["_trace_note"] = f"{len(value) - _MAX_TRACE_ITEMS} additional fields omitted"
        return cleaned
    if isinstance(value, (list, tuple, set)):
        seq = list(value)
        cleaned = [_safe_value(v) for v in seq[:_MAX_TRACE_ITEMS]]
        if len(seq) > _MAX_TRACE_ITEMS:
            cleaned.append(f"[{len(seq) - _MAX_TRACE_ITEMS} additional items omitted]")
        return cleaned
    if isinstance(value, str):
        if len(value) > _MAX_TRACE_STRING:
            return value[:_MAX_TRACE_STRING] + f"\n[trace truncated: {len(value) - _MAX_TRACE_STRING} chars omitted]"
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def sanitize_trace_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    """LangSmith ``process_inputs`` callback for custom spans."""
    return _safe_value(inputs)


def sanitize_trace_outputs(outputs: Any) -> dict[str, Any]:
    """LangSmith ``process_outputs`` callback for custom spans."""
    cleaned = _safe_value(outputs)
    return cleaned if isinstance(cleaned, dict) else {"result": cleaned}


def traceable(*args: Any, **kwargs: Any):
    """Privacy-aware wrapper around LangSmith's ``traceable`` decorator."""
    if _langsmith_traceable is None:
        # Support both ``@traceable`` and ``@traceable(name=...)`` styles.
        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return args[0]

        def decorator(func):
            return func

        return decorator

    kwargs.setdefault("process_inputs", sanitize_trace_inputs)
    kwargs.setdefault("process_outputs", sanitize_trace_outputs)
    return _langsmith_traceable(*args, **kwargs)


class TracedThreadPoolExecutor(ThreadPoolExecutor):
    """Copy the current tracing context separately for every worker task."""

    def submit(self, fn, /, *args, **kwargs):
        context = copy_context()
        return super().submit(context.run, fn, *args, **kwargs)
