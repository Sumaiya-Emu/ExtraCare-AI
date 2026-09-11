"""Deterministic hazard-scoring algorithm (pure Python, no LLM calls)."""
from typing import List, Tuple

from backend.config import settings
from backend.core.tracing import traceable
from backend.models.schemas import ClinicalFlag

_SEVERITY_PENALTY = {"info": 0, "caution": 15, "danger": 35}


@traceable("tool", name="risk_engine.calculate_hazard_score", tags=["deterministic", "risk"])
def calculate_hazard_score(flags: List[ClinicalFlag]) -> Tuple[int, str, str]:
    """Return a heuristic safety/compatibility score, not a probability of harm.

    Confidence gating happens *before* this function. Therefore ``no flags`` is only allowed to
    become 100/Safe after the system has already established that readable input was available.
    """
    score = 100
    ceiling = 100
    for flag in flags:
        score -= _SEVERITY_PENALTY.get(flag.severity, 0)
        if flag.severity == "danger":
            ceiling = min(ceiling, 35)
        elif flag.severity == "caution":
            ceiling = min(ceiling, 70)
    score = max(0, min(score, ceiling))

    if score >= settings.SAFE_THRESHOLD:
        verdict = "Safe"
    elif score >= settings.CAUTION_THRESHOLD:
        verdict = "Caution"
    else:
        verdict = "Toxic"
    return score, verdict, settings.RISK_TONES[verdict]
