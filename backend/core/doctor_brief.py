"""Generate a concise, non-diagnostic clinician handoff from already-produced structured data."""
from __future__ import annotations

from backend.models.schemas import CareDelta, PatientProfile, PipelineOutput


def build_doctor_brief(profile: PatientProfile, output: PipelineOutput, delta: CareDelta | None = None) -> str:
    report = output.report
    if report is None:
        return "ExtraCare AI could not produce a reliable assessment for this input. Please review the original document directly."

    lines = [
        "# ExtraCare AI — Doctor Visit Brief",
        "",
        "> Educational decision-support summary; not a diagnosis or treatment plan.",
        "",
        "## Patient context",
        f"- Age: {profile.age}",
        f"- Gender: {profile.gender}",
        f"- Pregnancy: {'Yes' if profile.is_pregnant else 'No'}",
        f"- Chronic conditions: {', '.join(profile.chronic_conditions) or 'None listed'}",
        f"- Known allergies: {', '.join(profile.known_allergies) or 'None listed'}",
        f"- Current medications: {', '.join(profile.current_medications) or 'None listed'}",
        "",
        "## Current assessment",
        f"- Heuristic concern score: {100 - report.safety_score}/100",
        f"- Interaction/finding category: {report.verdict}",
        f"- Confidence: {output.confidence.level.title()} ({output.confidence.score}/100)",
        f"- Extracted context: {output.extracted_summary or 'n/a'}",
        f"- Underlying report attention: {(output.underlying_clinical_attention or 'not applicable').replace('_', ' ')}",
        "",
        "## Flagged findings",
    ]
    if report.flags:
        for flag in report.flags:
            lines.append(f"- **{flag.item} — {flag.severity.upper()}**: {flag.mechanism}")
    else:
        lines.append("- No caution/danger flags were generated from the readable input.")

    if delta and delta.items:
        lines.extend(["", "## What changed since the previous session report"])
        for item in delta.items:
            if item.direction in {"unchanged", "new", "missing"}:
                continue
            if item.previous_value is not None or item.current_value is not None:
                lines.append(
                    f"- {item.name}: {item.previous_value} → {item.current_value} {item.unit or ''} ({item.direction})"
                )
            else:
                lines.append(f"- {item.name}: {item.previous_text} → {item.current_text} ({item.direction})")

    if report.specialist_recommendations:
        lines.extend(["", "## Suggested department(s) for discussion"])
        for rec in report.specialist_recommendations:
            lines.append(f"- {rec.department}: {rec.rationale}")

    lines.extend(["", "## Questions to discuss with a clinician"])
    questions = report.clinician_questions or [report.doctor_note]
    for question in questions:
        lines.append(f"- {question}")

    lines.extend(["", "## AI-generated consultation note", report.doctor_note])
    return "\n".join(lines)
