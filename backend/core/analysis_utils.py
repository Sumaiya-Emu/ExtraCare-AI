"""Shared parsing/evidence helpers for specialist agents."""
from __future__ import annotations

import re
from typing import Iterable

from backend.core.errors import AnalysisParsingError
from backend.core.evidence_registry import allows_absolute_restriction, allows_numeric_threshold
from backend.core.json_extract import JSONExtractionError, extract_json_object
from backend.models.schemas import AnalysisResult, EvidenceKind

_SOURCE_RE = re.compile(r"Source:\s*([^\n.]+(?:\.[^\n]*)?)", re.IGNORECASE)


def extract_sources(chunks: Iterable[str]) -> list[str]:
    sources: list[str] = []
    for chunk in chunks:
        for match in _SOURCE_RE.findall(chunk):
            value = match.strip().rstrip(".")
            if value and value.lower() != "unspecified" and value not in sources:
                sources.append(value)
    return sources


def parse_analysis_response(
    content,
    *,
    base_tags: list[EvidenceKind],
    context_chunks: Iterable[str] = (),
    used_live_search: bool = False,
) -> AnalysisResult:
    """Parse required JSON and attach provenance tags deterministically.

    Parsing failure is a hard failure; callers must never replace it with empty flags because that
    would allow the risk engine to convert an unparseable model response into a false ``Safe``.
    """
    try:
        payload = extract_json_object(content)
        if not isinstance(payload.get("flags"), list) or not isinstance(payload.get("summary"), str) or not payload["summary"].strip():
            raise ValueError("Required flags and meaningful summary are missing")
        result = AnalysisResult(**payload)
    except (JSONExtractionError, ValueError, TypeError) as exc:
        raise AnalysisParsingError("The AI response could not be validated. Please retry the analysis.") from exc

    context_list = list(context_chunks)
    context_text = "\n".join(context_list).lower()
    tags = [tag for tag in dict.fromkeys(base_tags) if tag != "rag" or context_list]
    for flag in result.flags:
        flag.evidence_tags = list(dict.fromkeys(["ai_synthesis", *tags]))
        # A source name copied by the model is kept only when it is actually present in retrieved
        # evidence. Live-search provenance is tracked globally instead of being stamped onto every flag.
        if flag.source and flag.source.casefold() not in context_text:
            flag.source = None

        # Code-level fake-precision guard: a numeric restriction threshold survives only when
        # the same number is actually present in retrieved local evidence. Live search is useful
        # for recalls/current context, but it is deliberately not trusted as the sole dose source.
        for restriction in flag.restrictions:
            if restriction.source and restriction.source.casefold() not in context_text:
                restriction.source = None
            if restriction.classification == "fully_restricted" and not allows_absolute_restriction(restriction.source):
                restriction.classification = "partially_restricted"
                flag.severity = "caution" if flag.severity == "danger" else flag.severity
                note = "Absolute restriction downgraded because the bundled source is not in the verified high-stakes registry."
                flag.evidence_note = f"{flag.evidence_note} {note}".strip() if flag.evidence_note else note
            for field_name in ("tolerated_dose", "danger_threshold"):
                value = getattr(restriction, field_name)
                if not value:
                    continue
                numbers = re.findall(r"\d+(?:\.\d+)?", value)
                if numbers and (
                    not restriction.source
                    or not allows_numeric_threshold(restriction.source)
                    or not any(restriction.source.casefold() in chunk.casefold() and value.casefold() in chunk.casefold() for chunk in context_list)
                ):
                    setattr(restriction, field_name, None)
                    restriction.threshold_status = "unknown"

    result.retrieved_sources = list(dict.fromkeys(extract_sources(context_list)))
    result.used_live_search = used_live_search
    return result


def invoke_analysis_with_retry(
    model,
    prompt: str,
    *,
    base_tags: list[EvidenceKind],
    context_chunks: Iterable[str] = (),
    used_live_search: bool = False,
) -> AnalysisResult:
    """Invoke once, then perform one strict JSON-repair retry only if parsing fails.

    Normal successful requests keep the same latency. The second API call happens only when
    Groq model returned malformed/non-schema JSON, which avoids a frustrating manual retry.
    """
    response = model.invoke(prompt)
    try:
        return parse_analysis_response(
            response.content,
            base_tags=base_tags,
            context_chunks=context_chunks,
            used_live_search=used_live_search,
        )
    except AnalysisParsingError:
        repair_prompt = f"""
Your previous answer could not be validated as the required JSON schema.
Return ONLY one valid JSON object. No markdown fences, no commentary, no trailing text.
Do not add facts, thresholds, diagnoses, or sources that were not present in the original request.

Required top-level shape:
{{"flags": [{{"item": "...", "severity": "info|caution|danger", "mechanism": "...",
"source": null, "restrictions": [], "evidence_tags": ["ai_synthesis"]}}], "summary": "..."}}

ORIGINAL REQUEST:
{prompt}

PREVIOUS INVALID ANSWER:
{response.content}
"""
        repaired = model.invoke(repair_prompt)
        return parse_analysis_response(
            repaired.content,
            base_tags=base_tags,
            context_chunks=context_chunks,
            used_live_search=used_live_search,
        )
