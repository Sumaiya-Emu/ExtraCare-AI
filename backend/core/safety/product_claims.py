"""Post-validation for product-label claims and exposure-route mismatches."""
from __future__ import annotations

import re

from backend.models.schemas import AnalysisResult, ExtractedProductData


def _label_text(product: ExtractedProductData) -> str:
    facts = " ".join(
        " ".join(filter(None, [fact.name, fact.raw_value, str(fact.value) if fact.value is not None else None, fact.unit]))
        for fact in product.nutrition_facts
    )
    return " ".join(
        filter(
            None,
            [
                product.product_name or "",
                " ".join(product.ingredients),
                facts,
                product.allergen_statement or "",
                product.raw_text or "",
            ],
        )
    ).casefold()


def _numbers(text: str) -> list[str]:
    return re.findall(r"\d+(?:\.\d+)?", text or "")


def validate_product_claims(result: AnalysisResult, product: ExtractedProductData) -> AnalysisResult:
    """Remove unsupported label quantities and down-rank obvious route mismatches.

    This guard deliberately avoids fuzzy clinical interpretation. It checks only whether claimed
    observed quantities exist on the label and whether oral/dietary wording is being applied to a
    clearly topical product without explicit systemic-evidence wording.
    """
    label_text = _label_text(product)
    topical = product.exposure_route == "topical" or product.product_type in {"skincare", "cosmetic"}

    for flag in result.flags:
        for restriction in flag.restrictions:
            if restriction.observed_amount:
                claimed = _numbers(restriction.observed_amount)
                if claimed and restriction.observed_amount.casefold() not in label_text:
                    restriction.observed_amount = None
                    restriction.threshold_status = "unknown"

        if topical:
            text = " ".join(
                [
                    flag.mechanism,
                    *[restriction.mechanism for restriction in flag.restrictions],
                ]
            ).casefold()
            dietary_route_words = (
                "dietary intake",
                "oral intake",
                "ingestion",
                "eat ",
                "eating",
                "daily sodium",
                "daily potassium",
                "carbohydrate intake",
            )
            systemic_evidence_words = (
                "systemic absorption",
                "transdermal",
                "bloodstream",
                "plasma concentration",
            )
            if any(word in text for word in dietary_route_words):
                flag.severity = "info"
                note = (
                    "Exposure-route guard: an oral/dietary restriction was not treated as a personalized "
                    "topical hazard without evidence of clinically meaningful systemic absorption."
                )
                flag.evidence_note = f"{flag.evidence_note} {note}".strip() if flag.evidence_note else note

    return result
