"""Deterministic trust policy for bundled evidence labels.

High-stakes features such as numeric thresholds and absolute restrictions are allowed only when the
source label matches a pattern explicitly listed in ``data/knowledge_base/source_registry.json``.
This keeps the policy auditable and prevents prompt-only provenance from becoming trusted evidence.
"""
from __future__ import annotations

import json
from functools import lru_cache

from backend.config import settings

_UNTRUSTED_MARKERS = (
    "not independently re-verified",
    "contested",
    "general clinical",
    "general nutrition",
    "webmd",
    "standard endocrinology",
)


@lru_cache(maxsize=1)
def _verified_patterns() -> tuple[str, ...]:
    path = settings.KNOWLEDGE_BASE_DIR / "source_registry.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return ()
    values = payload.get("verified_source_patterns", []) if isinstance(payload, dict) else []
    return tuple(str(value).casefold().strip() for value in values if str(value).strip())


def is_source_verified(source: str | None) -> bool:
    if not source:
        return False
    value = source.casefold().strip()
    if any(marker in value for marker in _UNTRUSTED_MARKERS):
        return False
    return value in _verified_patterns()


def allows_numeric_threshold(source: str | None) -> bool:
    return is_source_verified(source)


def allows_absolute_restriction(source: str | None) -> bool:
    return is_source_verified(source)
