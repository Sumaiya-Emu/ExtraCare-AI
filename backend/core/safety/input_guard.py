"""Input consistency checks that fail closed before personalized clinical interpretation."""
from __future__ import annotations

from backend.core.errors import AnalysisUnavailableError
from backend.models.schemas import ExtractedLabData, ExtractedProductData, PatientProfile


def validate_profile_consistency(lab: ExtractedLabData, profile: PatientProfile) -> list[str]:
    """Block explicit report/profile demographic contradictions.

    The OCR prompt is instructed to populate report demographics only when visibly printed. Missing
    demographics never cause a failure because many lab reports omit them.
    """
    warnings: list[str] = []
    if lab.reported_age is not None and lab.reported_age != profile.age:
        raise AnalysisUnavailableError(
            f"The report explicitly lists age {lab.reported_age}, but the health profile is age "
            f"{profile.age}. Update the profile or upload the correct report before personalized analysis."
        )
    if lab.reported_gender is not None and lab.reported_gender != profile.gender:
        raise AnalysisUnavailableError(
            f"The report explicitly lists gender {lab.reported_gender}, but the health profile is "
            f"{profile.gender}. Update the profile or upload the correct report before personalized analysis."
        )
    if lab.reported_age is None and lab.reported_gender is None:
        warnings.append(
            "Report demographics were not visibly available, so the entered profile could not be cross-verified against the document."
        )
    return warnings


def validate_expected_product_type(product: ExtractedProductData, expected: str | None) -> list[str]:
    """Prevent obvious food/skincare cross-mode errors while allowing uncertain OCR to continue cautiously."""
    if not expected:
        return []
    expected = expected.casefold().strip()
    actual = product.product_type
    if (expected == "food" and product.exposure_route == "topical") or (expected == "skincare" and product.exposure_route == "oral"):
        raise AnalysisUnavailableError("The visible exposure route does not match the selected food/skincare workflow.")
    if actual == "unknown":
        return ["Product type could not be confirmed from the visible label; interpretation is limited to extracted ingredients/facts."]

    if expected == "food" and actual not in {"food", "supplement"}:
        raise AnalysisUnavailableError(
            f"This upload appears to be a {actual} product, not a food label. Use the appropriate product/skincare workflow."
        )
    if expected == "skincare" and actual not in {"skincare", "cosmetic"}:
        raise AnalysisUnavailableError(
            f"This upload appears to be a {actual} product, not a skincare/cosmetic label. Use Food Cross-Match or Product Sentinel instead."
        )
    return []
