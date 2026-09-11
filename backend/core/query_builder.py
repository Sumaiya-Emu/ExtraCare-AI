"""Shared profile-aware retrieval query construction.

Used by every agent that queries the vector store, so a patient's conditions and
pregnancy status always shape *what gets retrieved*, not just what the LLM is told
afterward. Factored out once three agents needed the same pattern.
"""
from backend.models.schemas import PatientProfile


def build_profile_aware_query(base_terms: str, profile: PatientProfile, fallback: str) -> str:
    condition_terms = ", ".join(profile.chronic_conditions)
    pregnancy_term = "pregnancy" if profile.is_pregnant else ""
    combined = ", ".join(t for t in [base_terms, condition_terms, pregnancy_term] if t)
    return combined or fallback


def adaptive_retrieval_k(item_count: int, base_k: int = 4, max_k: int = 12) -> int:
    """A query built by joining many ingredient names into one string dilutes a fixed k=4
    retrieval down to whichever handful of knowledge-base entries dominate the combined
    semantic signal — a 100-ingredient product would retrieve the same k as a 3-ingredient
    one. Scale k with how many items are actually being checked, capped well below "return
    the whole knowledge base" so retrieval still means something."""
    return min(max_k, max(base_k, item_count // 5))
