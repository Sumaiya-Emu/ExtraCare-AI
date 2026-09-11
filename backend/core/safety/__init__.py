"""Deterministic clinical-safety guardrails."""

from backend.core.safety.clinical_attention import assess_underlying_clinical_attention
from backend.core.safety.input_guard import validate_expected_product_type, validate_profile_consistency
from backend.core.safety.personalization import demote_general_only_flags
from backend.core.safety.product_claims import validate_product_claims

__all__ = [
    "assess_underlying_clinical_attention",
    "validate_expected_product_type",
    "validate_profile_consistency",
    "demote_general_only_flags",
    "validate_product_claims",
]
