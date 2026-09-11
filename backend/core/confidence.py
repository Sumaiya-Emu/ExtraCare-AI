"""Deterministic confidence gate.

The gate answers a different question from the hazard score: *is there enough trustworthy input to
show any safety verdict at all?* A low-confidence extraction never becomes ``Safe`` merely because
no flags were generated.
"""
from backend.core.tracing import traceable
from backend.models.schemas import AnalysisConfidence, ExtractedLabData, ExtractedProductData


def _finish(score: int, reasons: list[str]) -> AnalysisConfidence:
    score = max(0, min(100, score))
    if score < 50:
        level = "low"
    elif score < 80:
        level = "medium"
    else:
        level = "high"
    return AnalysisConfidence(level=level, score=score, reasons=reasons, can_show_verdict=score >= 50)


@traceable("tool", name="confidence.lab", tags=["confidence-gate"])
def assess_lab_confidence(data: ExtractedLabData) -> AnalysisConfidence:
    usable = [b for b in data.biomarkers if b.name.strip() and (b.value is not None or (b.qualitative_value or "").strip())]
    findings = [f for f in data.radiology_findings if f.finding.strip()]
    if not usable and not findings:
        return _finish(10, ["No structured laboratory values or written radiology findings were readable."])

    score = 95
    reasons: list[str] = []

    if data.document_type == "unknown":
        score -= 15
        reasons.append("The diagnostic document type could not be identified confidently.")

    if data.biomarkers:
        missing_units = sum(1 for b in data.biomarkers if not b.unit and b.value is not None)
        if missing_units:
            penalty = min(20, missing_units * 4)
            score -= penalty
            reasons.append(f"{missing_units} numeric result(s) were extracted without a unit.")

        empty_values = sum(1 for b in data.biomarkers if b.value is None and not b.qualitative_value)
        if empty_values:
            score -= min(25, empty_values * 6)
            reasons.append(f"{empty_values} biomarker row(s) had no usable numeric or qualitative value.")

    raw = data.raw_text.lower()
    if any(term in raw for term in ("unreadable", "illegible", "blurred", "unclear")):
        score = min(score, 45)
        reasons.append("The OCR text indicates that part of the document may be unreadable.")

    if data.was_truncated:
        score = min(score, 45)
        reasons.append(f"Only {data.pages_analyzed} of {data.pages_total} PDF pages were analyzed because of the configured page cap.")
    elif data.pages_analyzed > 1:
        reasons.append(f"All {data.pages_analyzed} PDF pages were analyzed together.")

    if not reasons:
        reasons.append("Structured diagnostic data was extracted with no obvious completeness warning.")
    return _finish(score, reasons)


@traceable("tool", name="confidence.product", tags=["confidence-gate"])
def assess_product_confidence(data: ExtractedProductData) -> AnalysisConfidence:
    if not any(item.strip() for item in data.ingredients):
        return _finish(20, ["No ingredient list was reliably extracted; a product-safety verdict would be misleading."])

    score = 92
    reasons: list[str] = []
    if len(data.ingredients) <= 2:
        score -= 12
        reasons.append("Only a very short ingredient list was extracted; verify that the full label is visible.")

    raw = data.raw_text.lower()
    if any(term in raw for term in ("unreadable", "illegible", "blurred", "unclear")):
        score = min(score, 45)
        reasons.append("The OCR text indicates that part of the label may be unreadable.")

    if data.was_truncated:
        score = min(score, 45)
        reasons.append(f"Only {data.pages_analyzed} of {data.pages_total} PDF pages were analyzed because of the configured page cap.")
    elif data.pages_analyzed > 1:
        reasons.append(f"All {data.pages_analyzed} PDF pages were analyzed together.")

    if not reasons:
        reasons.append("A structured ingredient list was extracted with no obvious completeness warning.")
    return _finish(score, reasons)


@traceable("tool", name="confidence.text", tags=["confidence-gate"])
def assess_text_confidence(text: str) -> AnalysisConfidence:
    cleaned = text.strip()
    if len(cleaned) < 2:
        return _finish(0, ["No usable ingredient or product text was provided."])
    if len(cleaned) < 4:
        return _finish(60, ["The typed input is very short; verify that the ingredient/product name is complete."])
    return _finish(90, ["Typed input bypasses OCR, reducing image-readability uncertainty."])
