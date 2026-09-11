"""Evidence guardrails for Disease Care & Protocol Hub output."""
from __future__ import annotations

import re

from backend.models.schemas import DiseaseProtocol

_DEFAULT_INTERVAL = "Individualized clinician-directed interval"


def _numbers(value: str | None) -> list[str]:
    return re.findall(r"\d+(?:\.\d+)?", value or "")


def validate_disease_protocol(protocol: DiseaseProtocol, evidence_text: str) -> DiseaseProtocol:
    """Strip unsupported precision and source labels from generated educational protocols."""
    evidence = (evidence_text or "").casefold()

    for collection in (protocol.strict_restrictions, protocol.recommended_increases):
        for item in collection:
            if item.target_or_limit:
                numbers = _numbers(item.target_or_limit)
                if not item.source or item.source.casefold() not in evidence or item.target_or_limit.casefold() not in evidence:
                    item.target_or_limit = None
            if item.source and item.source.casefold() not in evidence:
                item.source = None

    for test in protocol.diagnostic_tests:
        interval = test.interval or _DEFAULT_INTERVAL
        numbers = _numbers(interval)
        if interval != _DEFAULT_INTERVAL and (not test.source or test.source.casefold() not in evidence or interval.casefold() not in evidence):
            test.interval = _DEFAULT_INTERVAL
        if test.source and test.source.casefold() not in evidence:
            test.source = None

    protocol.evidence_sources = [
        source for source in protocol.evidence_sources if source and source.casefold() in evidence
    ]
    return protocol
