"""CKD-EPI 2021 (race-free) eGFR calculation — deterministic kidney-function context.

Source note: this course project uses the published 2021 creatinine equation coefficients. The
calculation is intentionally gated for populations where this adult equation should not be used by
this prototype (age <18 and pregnancy).
"""
import math
from typing import Literal

from backend.models.schemas import Biomarker, ExtractedLabData, PatientProfile


def calculate_egfr(creatinine_mg_dl: float, age: int, sex: Literal["Male", "Female"]) -> float:
    if not math.isfinite(creatinine_mg_dl) or creatinine_mg_dl <= 0 or age < 18 or sex not in {"Male", "Female"}:
        raise ValueError("eGFR requires positive finite serum creatinine, adult age, and a supported sex coefficient.")
    if sex == "Female":
        kappa, alpha, sex_multiplier = 0.7, -0.241, 1.012
    else:
        kappa, alpha, sex_multiplier = 0.9, -0.302, 1.0

    ratio = creatinine_mg_dl / kappa
    egfr = 142 * min(ratio, 1) ** alpha * max(ratio, 1) ** -1.200 * (0.9938**age) * sex_multiplier
    return round(egfr, 1)


def stage_from_egfr(egfr: float) -> str:
    if egfr >= 90:
        return "G1 (normal/high)"
    if egfr >= 60:
        return "G2 (mildly decreased)"
    if egfr >= 45:
        return "G3a (mildly-moderately decreased)"
    if egfr >= 30:
        return "G3b (moderately-severely decreased)"
    if egfr >= 15:
        return "G4 (severely decreased)"
    return "G5 (kidney failure)"


def augment_with_egfr(extracted: ExtractedLabData, profile: PatientProfile) -> bool:
    """Add eGFR when a usable creatinine value exists; return whether it was added."""
    if profile.age < 18 or profile.is_pregnant:
        return False

    if any("egfr (calculated" in b.name.casefold() for b in extracted.biomarkers):
        return False
    for biomarker in list(extracted.biomarkers):
        if "creatinine" not in biomarker.name.lower() or biomarker.value is None:
            continue
        unit = (biomarker.unit or "").lower().replace(" ", "")
        context = f"{biomarker.name} {biomarker.specimen or ''}".casefold()
        if any(term in context for term in ("urine", "urinary", "ratio", "clearance")):
            continue
        if unit not in {"mg/dl", "mgdl"} or not math.isfinite(biomarker.value) or biomarker.value <= 0:
            continue
        if extracted.document_type == "urinalysis" and not any(term in context for term in ("serum", "plasma", "blood")):
            continue
        if biomarker.raw_value and any(symbol in biomarker.raw_value for symbol in ("<", ">", "≤", "≥")):
            continue
        egfr = calculate_egfr(biomarker.value, profile.age, profile.gender)
        extracted.biomarkers.append(
            Biomarker(
                name="eGFR (calculated, CKD-EPI 2021)",
                value=egfr,
                unit="mL/min/1.73m2",
                reference_range=stage_from_egfr(egfr),
                specimen="calculated from serum creatinine",
            )
        )
        return True
    return False
