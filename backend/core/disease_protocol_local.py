"""Zero-network Disease Care Hub fallback built only from bundled structured evidence."""
from __future__ import annotations

from backend.config import settings
from backend.models.schemas import DiseaseProtocol

def _normalize_condition_name(value: str) -> str:
    import re
    clean = re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()
    aliases = {
        "type 2 diabetes mellitus": "diabetes mellitus type 2",
        "type 2 diabetes": "diabetes mellitus type 2",
        "diabetes": "diabetes mellitus type 2",
        "ckd": "chronic kidney disease ckd",
        "chronic kidney disease": "chronic kidney disease ckd",
        "fatty liver": "liver disease incl fatty liver",
        "nafld": "liver disease incl fatty liver",
        "celiac": "celiac disease",
        "high blood pressure": "hypertension",
    }
    return aliases.get(clean, clean)


def generate_local_disease_protocol(disease_name: str) -> DiseaseProtocol:
    """Build a zero-network educational protocol from the bundled structured KB.

    This is the Fast-mode safety fallback.  It deliberately avoids inventing lifestyle advice,
    numeric targets, or monitoring intervals that are absent from the local evidence.
    """
    import json

    from backend.models.schemas import DiagnosticTest, NutritionGuidance

    target = _normalize_condition_name(disease_name)
    path = settings.KNOWLEDGE_BASE_DIR / "clinical_guidelines.json"
    with open(path, encoding="utf-8") as fh:
        entries = [e for e in json.load(fh) if isinstance(e, dict) and e.get("condition")]

    if not target or len(target) < 3:
        return DiseaseProtocol(disease_name=disease_name, summary="Enter a specific disease or condition name.")
    matches = []
    target_tokens = set(target.split())
    for entry in entries:
        normalized = _normalize_condition_name(entry.get("condition", ""))
        entry_tokens = set(normalized.split())
        if normalized == target:
            matches.append(entry)

    if not matches:
        return DiseaseProtocol(
            disease_name=disease_name,
            summary=(
                "Fast mode did not find a close curated entry for this condition in the bundled "
                "knowledge base. Switch to Thorough mode for an AI-generated RAG-grounded overview, "
                "or add a verified guideline entry to the local knowledge base."
            ),
            used_live_search=False,
        )

    restrictions = []
    tests = []
    sources = []
    seen_restrictions = set()
    seen_tests = set()
    for entry in matches:
        source = entry.get("source") or None
        if source:
            sources.append(source)
        dietary = (entry.get("dietary_restriction") or "").strip()
        biomarker = (entry.get("biomarker") or "Relevant clinical marker").strip()
        if dietary and dietary.casefold() not in seen_restrictions:
            restrictions.append(
                NutritionGuidance(
                    item=f"Dietary precaution related to {biomarker}",
                    reason=dietary,
                    target_or_limit=None,
                    source=source,
                )
            )
            seen_restrictions.add(dietary.casefold())
        if biomarker and biomarker.casefold() not in seen_tests and "general precaution" not in biomarker.casefold():
            tests.append(
                DiagnosticTest(
                    test_name=biomarker,
                    interval="Individualized clinician-directed interval",
                    reasoning=(
                        f"The bundled evidence includes condition-specific interpretation ranges for {biomarker}; "
                        "follow-up frequency depends on severity, treatment, and clinician assessment."
                    ),
                    source=source,
                )
            )
            seen_tests.add(biomarker.casefold())

    condition_label = matches[0].get("condition", disease_name)
    return DiseaseProtocol(
        disease_name=disease_name,
        lifestyle_habits=[
            "Follow the monitoring and treatment plan provided by your clinician; this Fast-mode view only summarizes bundled educational evidence.",
            "Bring medication, supplement, and recent laboratory information to clinical follow-up so recommendations can be individualized.",
        ],
        strict_restrictions=restrictions,
        recommended_increases=[],
        diagnostic_tests=tests,
        summary=(
            f"Fast mode matched {condition_label} to {len(matches)} bundled evidence record(s). "
            "The guidance below is intentionally conservative and does not infer a personalized treatment plan or fabricate unsupported numeric targets."
        ),
        evidence_sources=list(dict.fromkeys(sources)),
        used_live_search=False,
    )

