"""Conservative deterministic summary of how abnormal the uploaded report itself appears.

This is intentionally separate from product-interaction scoring so a low product concern cannot
hide a severely abnormal laboratory report. It is not a diagnosis or emergency triage system.
"""
from __future__ import annotations

from backend.models.schemas import ClinicalAttention, ExtractedLabData


def _name(marker_name: str) -> str:
    return marker_name.casefold().replace("-", " ")


def assess_underlying_clinical_attention(lab: ExtractedLabData | None) -> ClinicalAttention | None:
    if lab is None:
        return None

    attention: ClinicalAttention = "routine"
    ranks = {"routine": 0, "follow_up": 1, "high": 2, "urgent_review": 3}
    for marker in lab.biomarkers:
        name = _name(marker.name)
        flag = (marker.report_flag or "").casefold()

        if any(word in flag for word in ("critical", "panic", "alert")):
            return "urgent_review"
        if any(word in flag for word in ("high", "low", "abnormal")):
            attention = max((attention, "follow_up"), key=ranks.get)

        value = marker.value
        if value is None:
            continue
        # High-impact, broadly interpretable severity cues. They trigger "high" review rather than
        # a diagnosis or emergency instruction.
        unit = (marker.unit or "").casefold().replace(" ", "").replace("²", "2").replace("^", "")
        specimen = f"{name} {marker.specimen or ''}".casefold()
        if "egfr" in name and unit in {"ml/min/1.73m2", "ml/min/1.73m2."} and value < 30:
            attention = "high"
        elif "creatinine" in name and not any(t in specimen for t in ("urine", "urinary", "ratio")) and unit == "mg/dl" and value >= 3.0:
            attention = "high"
        elif ("hba1c" in name or "a1c" in name) and unit == "%" and value >= 8.0:
            attention = "high"
        elif ("fasting" in name and "glucose" in name) and unit == "mg/dl" and value >= 200:
            attention = "high"
        elif "hemoglobin" in name and "urine" not in specimen and unit == "g/dl" and value < 8.0:
            attention = "high"

    if lab.radiology_findings and attention == "routine":
        attention = "follow_up"
    return attention
