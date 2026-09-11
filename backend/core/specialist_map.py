"""Deterministic specialist/department mapping with profile-aware prioritization."""
from __future__ import annotations

import re

from backend.models.schemas import ClinicalFlag, PatientProfile, SpecialistRecommendation

_SPECIALIST_KEYWORDS = [
    ("Nephrology", ["kidney", "renal", "creatinine", "egfr", "uacr", "albuminuria", "proteinuria", "ckd"]),
    ("Endocrinology", ["hba1c", "glucose", "diabetes", "insulin", "thyroid", "tsh", "t3", "t4"]),
    ("Cardiology", ["hypertension", "blood pressure", "heart failure", "arrhythmia", "cardiac disease", "ldl", "cholesterol", "triglyceride"]),
    ("Hepatology / Gastroenterology", ["liver", "hepatomegaly", "fatty liver", "steatosis", "alt", "ast", "bilirubin"]),
    ("Hematology", ["hemoglobin", "anemia", "platelet", "wbc", "rbc", "leukocyte"]),
    ("Pulmonology", ["lung", "pulmonary", "bronch", "asthma", "pleural"]),
    ("Orthopedics", ["fracture", "degenerative", "osteoarthritis", "joint degeneration", "disc degeneration", "spondyl"]),
    ("Rheumatology", ["gout", "uric acid", "inflammatory joint"]),
    ("Urology", ["hematuria", "bladder", "prostate", "urinary obstruction"]),
    ("Dermatology", ["skin", "dermat", "rash", "eczema", "contact sensitivity"]),
    ("Allergy & Immunology", ["allergy", "allergic", "anaphylaxis", "anaphylactic", "peanut", "tree nut", "shellfish"]),
    ("Obstetrics / Gynecology", ["pregnan", "uterus", "ovary", "ovarian", "fetal", "placenta"]),
]


def _keyword_matches(text: str, keyword: str) -> bool:
    """Avoid substring accidents such as ALT matching the word 'salt'."""
    if len(keyword) <= 4 and keyword.replace(" ", "").isalpha():
        return re.search(rf"\b{re.escape(keyword)}\b", text) is not None
    return keyword in text


def _profile_has_cardiac_context(profile: PatientProfile | None) -> bool:
    if not profile:
        return False
    text = " ".join(profile.chronic_conditions).casefold()
    return any(k in text for k in ("hypertension", "heart", "cardiac", "arrhythm", "dyslip"))


def recommend_specialists(
    flags: list[ClinicalFlag],
    profile: PatientProfile | None = None,
    max_results: int = 3,
) -> list[SpecialistRecommendation]:
    candidates: dict[str, SpecialistRecommendation] = {}
    severity_rank = {"danger": 0, "caution": 1, "info": 2}

    if profile and profile.is_pregnant and flags:
        candidates["Obstetrics / Gynecology"] = SpecialistRecommendation(
            department="Obstetrics / Gynecology",
            rationale="Pregnancy changes the safety context of the flagged finding(s), so pregnancy-specific review is the most relevant clinical pathway.",
            triggered_by="Pregnancy context",
            priority="primary",
        )

    ordered = sorted(flags, key=lambda f: severity_rank.get(f.severity, 9))
    for flag in ordered:
        if flag.severity == "info":
            continue
        restriction_conditions = " ".join(r.condition for r in flag.restrictions)
        allergy_context = " ".join(profile.known_allergies) if profile else ""
        core_text = f"{flag.item} {restriction_conditions} {allergy_context}".casefold()
        full_text = f"{core_text} {flag.mechanism} " + " ".join(r.mechanism for r in flag.restrictions)
        full_text = full_text.casefold()

        for department, keywords in _SPECIALIST_KEYWORDS:
            if department in candidates:
                continue

            # Cardiology should reflect an actual cardiovascular condition/finding, not a downstream
            # phrase like 'may cause cardiac complications' inside a renal-food mechanism.
            if department == "Cardiology":
                explicit_cardio = any(
                    _keyword_matches(core_text, k)
                    for k in ("hypertension", "blood pressure", "heart failure", "arrhythmia", "cardiac disease", "ldl", "cholesterol", "triglyceride")
                )
                if not explicit_cardio and not _profile_has_cardiac_context(profile):
                    continue

            if not any(_keyword_matches(full_text, k) for k in keywords):
                continue
            if department == "Cardiology" and flag.item.casefold().strip() == "caffeine":
                continue

            candidates[department] = SpecialistRecommendation(
                department=department,
                rationale=f"{flag.item} ({flag.severity}) maps to the {department} domain and may merit clinician review.",
                triggered_by=flag.item,
                priority="secondary",
            )

    results = list(candidates.values())[:max_results]
    if results and not any(r.priority == "primary" for r in results):
        results[0].priority = "primary"
    return results


def recommend_specialist(flags: list[ClinicalFlag]) -> tuple[str | None, str | None]:
    """Backward-compatible single-specialist helper used by existing tests/callers."""
    recs = recommend_specialists(flags, profile=None, max_results=1)
    if not recs:
        return None, None
    return recs[0].department, recs[0].rationale
