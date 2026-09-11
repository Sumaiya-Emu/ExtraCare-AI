"""Deterministic restriction fast-path backed by the bundled toxicology JSON.

This is intentionally conservative. It only returns a result when *every* typed item maps to a
known curated entry and the user's relevant condition(s) have explicit restriction rules. Anything
unknown or ambiguous falls back to RAG + LLM analysis.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from backend.config import settings
from backend.core.tracing import traceable
from backend.core.evidence_registry import allows_absolute_restriction, allows_numeric_threshold
from backend.models.schemas import AnalysisResult, ClinicalFlag, PatientProfile, RestrictionRule


@lru_cache(maxsize=1)
def _entries() -> list[dict]:
    with open(settings.KNOWLEDGE_BASE_DIR / "toxicology_standards.json", encoding="utf-8") as f:
        return [e for e in json.load(f) if isinstance(e, dict) and "ingredient" in e]


def _split_items(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,;\n]+", text) if part.strip()]


def _match_entry(item: str) -> dict | None:
    needle = item.casefold().strip()
    if len(needle) < 3:
        return None
    aliases = {"gluten": "gluten", "peanut": "peanut", "salt": "sodium chloride"}
    needle = aliases.get(needle, needle)
    matches = [e for e in _entries() if needle in {
        e.get("ingredient", "").casefold(),
        *[part.strip() for part in re.split(r"[()/]", e.get("ingredient", "").casefold()) if part.strip()],
    }]
    # Avoid pretending an ambiguous word is an exact curated match.
    return matches[0] if len(matches) == 1 else None



@traceable("tool", name="restriction_engine.fast_path", tags=["deterministic", "restriction"])
def try_deterministic_restriction_check(text: str, profile: PatientProfile) -> AnalysisResult | None:
    items = _split_items(text)
    if not items:
        return None

    matched: list[tuple[str, dict]] = []
    for item in items:
        entry = _match_entry(item)
        if entry is None:
            return None
        matched.append((item, entry))

    effective_conditions = [*profile.chronic_conditions, *profile.known_allergies]
    if profile.is_pregnant:
        effective_conditions.append("Pregnancy")
    condition_keys = {c.casefold() for c in effective_conditions}

    flags: list[ClinicalFlag] = []
    for typed_item, entry in matched:
        raw_rules = entry.get("restriction_rules", [])
        if effective_conditions:
            selected_rules = [r for r in raw_rules if str(r.get("condition", "")).casefold() in condition_keys]
            # A known ingredient with no explicit rule for this profile is not proof of safety.
            if not selected_rules:
                return None
        else:
            # No profile disease selected: show the curated general condition contexts.
            selected_rules = raw_rules
            if not selected_rules:
                return None

        restrictions = [RestrictionRule(**rule) for rule in selected_rules]
        for restriction in restrictions:
            if restriction.classification == "fully_restricted" and not allows_absolute_restriction(restriction.source):
                return None
            for field_name in ("tolerated_dose", "danger_threshold"):
                value = getattr(restriction, field_name)
                if value and any(ch.isdigit() for ch in value) and not allows_numeric_threshold(restriction.source):
                    setattr(restriction, field_name, None)
                    restriction.threshold_status = "unknown"
        flags.append(
            ClinicalFlag(
                item=entry.get("ingredient", typed_item),
                severity="danger" if any(r.classification == "fully_restricted" for r in restrictions) else "caution",
                mechanism=entry.get("mechanism", "Known curated restriction rule."),
                source=entry.get("source"),
                restrictions=restrictions,
                evidence_tags=["deterministic"],
                evidence_note="Matched directly to a curated local restriction rule; ambiguous inputs fall back to RAG + LLM.",
            )
        )

    context = ", ".join(e.get("ingredient", item) for item, e in matched)
    if effective_conditions:
        summary = f"Deterministic fast-path match for {context} against the selected health profile."
    else:
        summary = f"Deterministic fast-path match for {context}; showing general condition-specific restriction rules because no chronic condition was selected."
    return AnalysisResult(
        flags=flags,
        summary=summary,
        retrieved_sources=list(dict.fromkeys(e.get("source") for _, e in matched if e.get("source"))),
        used_live_search=False,
    )
