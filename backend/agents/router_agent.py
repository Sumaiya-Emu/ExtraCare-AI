"""Supervisor/router: validates profile and confirms analysis mode."""
from backend.core.tracing import traceable
from backend.models.schemas import PatientProfile


class ProfileIncompleteError(ValueError):
    pass


@traceable("chain", name="router_agent.route", tags=["agent", "router"])
def route(mode: str, profile: PatientProfile) -> str:
    if mode not in ("lab", "product", "cross_match", "text_check"):
        raise ProfileIncompleteError(f"Unknown mode '{mode}'.")
    if profile.age <= 0:
        raise ProfileIncompleteError("Age must be set before analysis can run.")
    if profile.is_pregnant and profile.gender != "Female":
        raise ProfileIncompleteError("Pregnancy flag is inconsistent with the selected gender.")
    return mode
