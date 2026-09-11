"""Deterministic distinction between personalized restrictions and general condition education."""
from __future__ import annotations

from backend.models.schemas import AnalysisResult, PatientProfile


def _normalized_contexts(profile: PatientProfile) -> list[str]:
    values = [*profile.chronic_conditions, *profile.known_allergies]
    if profile.is_pregnant:
        values.append("Pregnancy")
    return [value.casefold().strip() for value in values if value.strip()]


def _matches(condition: str, contexts: list[str]) -> bool:
    needle = condition.casefold().strip()
    if not needle:
        return False
    return any(needle in context or context in needle for context in contexts)


def demote_general_only_flags(result: AnalysisResult, profile: PatientProfile) -> AnalysisResult:
    """Do not let a generic condition warning look like a personalized danger verdict.

    When the user has not declared the condition/allergy named by a restriction, the educational
    rule remains visible but contributes only informational severity. Cross-Match has separate
    report-derived context and therefore does not use this helper.
    """
    contexts = _normalized_contexts(profile)
    for flag in result.flags:
        if not flag.restrictions:
            continue
        if any(_matches(rule.condition, contexts) for rule in flag.restrictions):
            continue
        flag.severity = "info"
        note = "General condition context only; this restriction was not matched to the entered health profile."
        flag.evidence_note = f"{flag.evidence_note} {note}".strip() if flag.evidence_note else note
    return result
