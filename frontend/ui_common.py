"""Shared Streamlit UI components for ExtraCare AI.

This module is intentionally presentation-only: it renders widgets, owns session state/cache, and
calls backend controller functions. It does not call LLMs, RAG stores, search APIs, or clinical
algorithms directly.
"""
from __future__ import annotations

import hashlib
import html
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.config.catalog import CONDITION_OPTIONS
from backend.controllers import (
    analyze as controller_analyze,
    build_care_graph_dot,
    build_delta,
    build_visit_brief,
    ensure_knowledge_base_ready,
    generate_protocol as controller_generate_protocol,
    load_sample_asset,
    preview_document,
    startup_status,
)
from backend.models.schemas import CareDelta, DiseaseProtocol, ExtractedLabData, PatientProfile, PipelineOutput

VERDICT_BADGE_CLASS = {
    "Safe": "score-badge--safe",
    "Caution": "score-badge--caution",
    "Toxic": "score-badge--danger",
}
CONCERN_LABEL = {
    "Safe": "Low concern",
    "Caution": "Needs caution",
    "Toxic": "High concern / review",
}
SEVERITY_CARD_CLASS = {
    "info": "result-card--info",
    "caution": "result-card--caution",
    "danger": "result-card--danger",
}
EVIDENCE_LABELS = {
    "deterministic": "🧮 Deterministic calculation",
    "rag": "📚 RAG evidence",
    "live_search": "🌐 Live search",
    "ai_synthesis": "🤖 AI synthesis",
}
CLINICAL_ATTENTION_LABELS = {
    "routine": ("No high-attention rule matched", "clinical-attention--routine"),
    "follow_up": ("Follow-up recommended", "clinical-attention--follow-up"),
    "high": ("High clinical attention", "clinical-attention--high"),
    "urgent_review": ("Prompt clinical review", "clinical-attention--urgent"),
}


def _esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def load_css() -> None:
    """Load the external stylesheet without embedding CSS literals in Python."""
    css_path = Path(__file__).resolve().parent / "assets" / "style.css"
    st.html(css_path)


@st.cache_resource(show_spinner=False)
def ensure_knowledge_base() -> bool:
    return ensure_knowledge_base_ready()


def load_sample_image(filename: str) -> bytes:
    return load_sample_asset(filename)


def get_preview_bytes(data: bytes) -> bytes:
    return preview_document(data)


def sync_uploaded_document(uploaded, bytes_key: str, id_key: str, result_key: str) -> None:
    """Synchronize upload/removal without replacing a deliberately selected sample."""
    source_key = bytes_key + "_source"
    if uploaded is not None and st.session_state.get(id_key) != uploaded.file_id:
        st.session_state[bytes_key] = uploaded.getvalue()
        st.session_state[id_key] = uploaded.file_id
        st.session_state[source_key] = "upload"
        st.session_state.pop(result_key, None)
    elif uploaded is None and id_key in st.session_state:
        st.session_state.pop(id_key, None)
        if st.session_state.get(source_key) == "upload":
            st.session_state.pop(bytes_key, None)
            st.session_state.pop(source_key, None)
            st.session_state.pop(result_key, None)


def render_document_preview(data: bytes, **kwargs) -> None:
    try:
        st.image(get_preview_bytes(data), **kwargs)
    except Exception:
        st.error("This document could not be previewed. Upload a valid image or an unencrypted PDF.")


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="app-header">
            <p class="app-header__title">{_esc(title)}</p>
            <p class="app-header__subtitle">{_esc(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _merge_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for value in values:
        clean = value.strip()
        key = clean.casefold()
        if clean and key not in seen:
            seen.add(key)
            merged.append(clean)
    return merged


def render_profile_sidebar() -> PatientProfile:
    for key in list(st.session_state):
        if key.startswith("profile_") or key == "analysis_speed_mode":
            st.session_state[key] = st.session_state[key]
    status = startup_status()
    st.sidebar.markdown('<p class="sidebar-brand">ExtraCare AI</p>', unsafe_allow_html=True)
    st.sidebar.caption("Personalized Health Intelligence & Safety Assistant")
    st.sidebar.markdown('<p class="section-label">Core Health Profile</p>', unsafe_allow_html=True)

    age = st.sidebar.number_input("Age", min_value=0, max_value=120, value=30, key="profile_age")
    gender = st.sidebar.selectbox(
        "Gender",
        ["Female", "Male"],
        key="profile_gender",
        help=(
            "For adult CKD-EPI eGFR, this educational prototype uses the selected value for the "
            "equation-specific coefficient. Reported eGFR is shown separately when present."
        ),
    )
    is_pregnant = st.sidebar.checkbox("Currently pregnant", key="profile_pregnant") if gender == "Female" else False

    st.sidebar.markdown('<p class="section-label">Chronic conditions</p>', unsafe_allow_html=True)
    selected = st.sidebar.multiselect(
        "Search/select all that apply",
        CONDITION_OPTIONS,
        key="profile_conditions",
        placeholder="Type to search conditions",
    )
    custom_raw = st.sidebar.text_input(
        "Add any condition not listed",
        placeholder="e.g. Migraine, Osteoporosis",
        key="profile_custom_conditions",
    )
    custom = [item.strip() for item in custom_raw.split(",") if item.strip()]
    conditions = _merge_unique([*selected, *custom])

    st.sidebar.markdown('<p class="section-label">Known allergies</p>', unsafe_allow_html=True)
    allergy_raw = st.sidebar.text_input(
        "Comma-separated, optional",
        placeholder="e.g. Peanut, Milk, Latex",
        key="profile_allergies",
    )
    allergies = _merge_unique([item for item in allergy_raw.split(",") if item.strip()])

    st.sidebar.markdown('<p class="section-label">Current medications</p>', unsafe_allow_html=True)
    meds_raw = st.sidebar.text_area(
        "Comma-separated, optional",
        placeholder="e.g. Metformin, Losartan",
        key="profile_meds",
        height=80,
    )
    medications = _merge_unique([item for item in meds_raw.split(",") if item.strip()])

    st.sidebar.markdown('<p class="section-label">Analysis speed</p>', unsafe_allow_html=True)
    default_mode = "🔎 Thorough" if status.get("default_analysis_mode") == "thorough" else "⚡ Fast"
    st.sidebar.radio(
        "Processing mode",
        ["⚡ Fast", "🔎 Thorough"],
        index=1 if default_mode == "🔎 Thorough" else 0,
        key="analysis_speed_mode",
        help=(
            "Fast gives you a quick answer using our built-in knowledge. Thorough also looks things "
            "up online when that's available, for a more detailed answer."
        ),
    )
    if st.session_state.get("analysis_speed_mode") == "🔎 Thorough" and not status.get("tavily"):
        st.sidebar.caption("Live web search isn't available right now; Thorough mode will use our built-in knowledge base instead.")
    st.sidebar.caption("Profile changes invalidate previously personalized results automatically.")

    missing = status.get("missing_required") or []
    if missing:
        st.sidebar.warning("Missing: " + ", ".join(missing) + ". Add a valid value to .env and restart Streamlit.")

    return PatientProfile(
        age=int(age),
        gender=gender,
        is_pregnant=is_pregnant,
        chronic_conditions=conditions,
        current_medications=medications,
        known_allergies=allergies,
    )


def profile_fingerprint(profile: PatientProfile) -> str:
    return hashlib.sha256(profile.model_dump_json().encode("utf-8")).hexdigest()


def _hash_bytes(data: Optional[bytes]) -> str:
    return hashlib.sha256(data or b"").hexdigest()


def analysis_fingerprint(
    mode: str,
    profile: PatientProfile,
    image_bytes: Optional[bytes] = None,
    product_image_bytes: Optional[bytes] = None,
    ingredients_text: Optional[str] = None,
    expected_product_type: Optional[str] = None,
) -> str:
    payload = "|".join(
        [
            "final-v1",
            mode,
            expected_product_type or "",
            profile_fingerprint(profile),
            _hash_bytes(image_bytes),
            _hash_bytes(product_image_bytes),
            (ingredients_text or "").strip(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _profile_summary(profile: PatientProfile) -> str:
    parts = [f"{profile.age}, {profile.gender}"]
    if profile.is_pregnant:
        parts.append("pregnant")
    parts.append(", ".join(profile.chronic_conditions) if profile.chronic_conditions else "no chronic conditions listed")
    if profile.known_allergies:
        parts.append("allergies: " + ", ".join(profile.known_allergies))
    return " | ".join(parts)


def _render_confidence(output: PipelineOutput) -> None:
    conf = output.confidence
    css_class = f"confidence-pill confidence-pill--{conf.level}"
    st.markdown(
        f'<span class="{css_class}">How complete is your information: {_esc(conf.level.title())} · {conf.score}/100</span>',
        unsafe_allow_html=True,
    )
    if conf.reasons:
        with st.expander("Confidence details"):
            for reason in conf.reasons:
                st.write(f"• {reason}")


def _render_clinical_attention(output: PipelineOutput) -> None:
    attention = output.underlying_clinical_attention
    if not attention:
        return
    label, css_class = CLINICAL_ATTENTION_LABELS.get(attention, (attention.replace("_", " ").title(), ""))
    st.markdown(
        f"""
        <div class="clinical-attention {css_class}">
            <span class="clinical-attention__label">Underlying report attention</span>
            <span class="clinical-attention__value">{_esc(label)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("This describes the uploaded report itself, separately from any food/product interaction score.")


def _format_fact(value: object, unit: Optional[str]) -> str:
    if value is None:
        return "—"
    if isinstance(value, (int, float)):
        return f"{value:g} {unit or ''}".strip()
    return f"{value} {unit or ''}".strip()


def _render_extracted_data(output: PipelineOutput) -> None:
    if output.extracted_lab:
        lab = output.extracted_lab
        demographics = []
        if lab.reported_age is not None:
            demographics.append(f"reported age {lab.reported_age}")
        if lab.reported_gender:
            demographics.append(f"reported gender {lab.reported_gender}")
        suffix = f" · {' · '.join(demographics)}" if demographics else ""
        st.caption(
            f"Detected document: {lab.document_type.replace('_', ' ').title()} · "
            f"pages: {lab.pages_analyzed}/{lab.pages_total} analyzed{suffix}"
        )
        if lab.biomarkers:
            rows = []
            for marker in lab.biomarkers:
                display = marker.raw_value or (
                    _format_fact(marker.value, marker.unit)
                    if marker.value is not None
                    else (marker.qualitative_value or "—")
                )
                rows.append(
                    {
                        "Biomarker / test": marker.name,
                        "Result": display,
                        "Reference": marker.reference_range or "—",
                        "Report flag": marker.report_flag or "—",
                        "Specimen": marker.specimen or "—",
                    }
                )
            st.dataframe(rows, hide_index=True, width="stretch")
        if lab.radiology_findings:
            st.markdown("**Written radiology findings extracted**")
            rows = [
                {
                    "Modality": finding.modality or "—",
                    "Body part": finding.body_part or "—",
                    "Finding": finding.finding,
                    "Impression": finding.impression or "—",
                    "Page": finding.source_page or "—",
                }
                for finding in lab.radiology_findings
            ]
            st.dataframe(rows, hide_index=True, width="stretch")

    if output.extracted_product:
        product = output.extracted_product
        st.caption(
            f"Product OCR pages: {product.pages_analyzed}/{product.pages_total} analyzed · "
            f"type: {product.product_type} · route: {product.exposure_route}"
        )
        if product.product_name:
            st.write(f"**Product:** {product.product_name}")
        if product.ingredients:
            st.write("**Ingredients:** " + ", ".join(product.ingredients))
        if product.allergen_statement:
            st.write(f"**Printed allergen statement:** {product.allergen_statement}")
        if product.nutrition_facts:
            rows = [
                {
                    "Fact": fact.name,
                    "Amount": fact.raw_value or _format_fact(fact.value, fact.unit),
                    "Basis": fact.per or "—",
                }
                for fact in product.nutrition_facts
            ]
            st.dataframe(rows, hide_index=True, width="stretch")


def _render_restriction(restriction) -> None:
    full = restriction.classification == "fully_restricted"
    badge = "FULLY RESTRICTED — COMPLETE AVOIDANCE" if full else "PARTIALLY RESTRICTED — DOSE/CONTEXT DEPENDENT"
    css_class = "flag-item__restriction--full" if full else "flag-item__restriction--partial"
    st.markdown(
        f'<span class="flag-item__restriction {css_class}">{_esc(badge)}</span>',
        unsafe_allow_html=True,
    )
    st.write(f"**Condition/context:** {restriction.condition}")
    st.write(restriction.mechanism)
    left, right = st.columns(2)
    with left:
        st.caption("Tolerated / recommended limit")
        st.write(restriction.tolerated_dose or "No verified universal threshold available")
    with right:
        st.caption("Danger / escalation threshold")
        st.write(restriction.danger_threshold or "No verified universal threshold available")
    if restriction.observed_amount:
        st.write(f"**Observed on label:** {restriction.observed_amount}")
    if restriction.threshold_status != "unknown":
        st.write(f"**Threshold comparison:** {restriction.threshold_status.replace('_', ' ').title()}")
    if restriction.source:
        st.caption(f"Source: {restriction.source}")


def _render_flag(flag, clinical_view: bool = False) -> None:
    card_class = SEVERITY_CARD_CLASS.get(flag.severity, "result-card--info")
    st.markdown(
        f"""
        <div class="result-card {card_class}">
            <span class="flag-item__label">{_esc(flag.item)}</span>
            <span class="flag-item__severity">{_esc(flag.severity.upper())}</span>
            <div class="flag-item__mechanism">{_esc(flag.mechanism)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if flag.evidence_note:
        st.caption(flag.evidence_note)
    if flag.restrictions:
        with st.expander(f"Restriction details · {flag.item}"):
            for restriction in flag.restrictions:
                _render_restriction(restriction)
                st.divider()
    if clinical_view:
        with st.expander(f"Why / evidence · {flag.item}"):
            tags = [EVIDENCE_LABELS.get(tag, tag) for tag in flag.evidence_tags]
            st.write(" · ".join(tags) if tags else "No provenance tags available")
            if flag.source:
                st.write(f"**Source:** {flag.source}")
            if flag.evidence_note:
                st.write(flag.evidence_note)


def render_care_delta(delta: CareDelta) -> None:
    if not delta.items:
        st.info("No comparable biomarkers were found between the two reports.")
        return
    st.markdown('<p class="section-label">CareDelta · What changed?</p>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Increased", delta.increased)
    col2.metric("Decreased", delta.decreased)
    col3.metric("Unchanged", delta.unchanged)
    col4.metric("Qualitative changes", delta.changed_qualitative)

    rows = []
    for item in delta.items:
        previous = item.previous_text if item.previous_text is not None else _format_fact(item.previous_value, item.unit)
        current = item.current_text if item.current_text is not None else _format_fact(item.current_value, item.unit)
        rows.append(
            {
                "Test": item.name,
                "Previous": previous,
                "Current": current,
                "Change": item.direction.replace("_", " ").title(),
                "% change": f"{item.percent_change:+.1f}%" if item.percent_change is not None else "—",
            }
        )
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption(
        "CareDelta reports direction of change, not whether a change is clinically better or worse. "
        "Interpretation depends on the test, units, and clinical context."
    )


def _score_context(output: PipelineOutput, report) -> tuple[int, str, str]:
    concern = 100 - report.safety_score
    has_absolute = any(
        restriction.classification == "fully_restricted"
        for flag in report.flags
        for restriction in flag.restrictions
    )
    if output.mode == "cross_match":
        scale = "/ 100 product–report concern"
    elif output.mode in {"product", "text_check"}:
        scale = "/ 100 product/ingredient concern"
    else:
        scale = "/ 100 report concern"

    verdict = "Strict avoidance indicated" if report.verdict == "Toxic" and has_absolute else CONCERN_LABEL.get(report.verdict, report.verdict)
    return concern, scale, verdict


def render_report(
    output: PipelineOutput,
    profile: PatientProfile,
    *,
    concern_display: bool = False,
    flags_heading: Optional[str] = None,
    view_key: str = "result",
    delta: Optional[CareDelta] = None,
) -> None:
    del concern_display  # Kept for backward-compatible page calls; all modules now show concern semantics.
    st.markdown(
        f'<p class="personalized-for">Personalized for: {_esc(_profile_summary(profile))}</p>',
        unsafe_allow_html=True,
    )
    _render_confidence(output)

    if output.warnings:
        for warning in output.warnings:
            st.warning(warning)

    if output.status != "ok" or output.report is None or not output.confidence.can_show_verdict:
        st.markdown(
            """
            <div class="confidence-gate confidence-gate--blocked">
                <strong>Unable to assess safely</strong><br>
                ExtraCare AI could not validate enough of this input to publish a personalized conclusion.
                Correct the issue shown above, use a clearer/complete document, or retry.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    report = output.report
    view = st.radio(
        "View",
        ["Patient view", "Clinical view"],
        horizontal=True,
        key=f"{view_key}_audience",
        label_visibility="collapsed",
    )
    clinical_view = view == "Clinical view"

    _render_clinical_attention(output)
    score_value, score_scale, score_verdict = _score_context(output, report)
    badge_class = VERDICT_BADGE_CLASS.get(report.verdict, "")
    st.markdown(
        f"""
        <div class="score-badge {badge_class}">
            <span class="score-badge__value">{score_value}</span>
            <span class="score-badge__scale">{_esc(score_scale)}</span>
            <span class="score-badge__verdict">{_esc(score_verdict)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Heuristic decision-support score — not a statistical probability of harm or a diagnosis.")

    if clinical_view:
        st.caption("Live search executed." if output.used_live_search else "Live search was not executed for this analysis.")
        if output.retrieved_sources:
            with st.expander("Retrieved evidence sources"):
                for source in output.retrieved_sources:
                    st.write(source)
        with st.expander("Extracted structured data", expanded=True):
            _render_extracted_data(output)
    elif output.extracted_summary:
        st.caption(f"Read from your input: {output.extracted_summary}")

    st.markdown(f'<div class="summary-block">{_esc(report.mechanism_summary)}</div>', unsafe_allow_html=True)

    if report.flags:
        heading = flags_heading or "Key findings"
        st.markdown(f'<p class="section-label">{_esc(heading)}</p>', unsafe_allow_html=True)
    for flag in report.flags:
        _render_flag(flag, clinical_view=clinical_view)

    if report.specialist_recommendations:
        st.markdown('<p class="section-label">Recommended Specialist / Clinical Department</p>', unsafe_allow_html=True)
        for recommendation in report.specialist_recommendations:
            st.markdown(
                f"""
                <div class="specialist-card">
                    <span class="specialist-card__label">{_esc(recommendation.priority.upper())}</span>
                    <span class="specialist-card__name">{_esc(recommendation.department)}</span>
                    <div class="specialist-card__rationale">{_esc(recommendation.rationale)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if delta is not None:
        render_care_delta(delta)

    if report.flags:
        with st.expander("CareGraph · See how your health context connects"):
            try:
                st.graphviz_chart(build_care_graph_dot(profile, report), width="stretch")
            except Exception:
                st.caption("CareGraph visualization is unavailable in this environment; the analysis remains valid.")

    if report.safe_alternatives:
        st.markdown('<p class="section-label">CareSwap · What to choose instead</p>', unsafe_allow_html=True)
        for alternative in report.safe_alternatives:
            st.write(f"• {alternative}")

    with st.expander("Prepare for a clinician visit", expanded=clinical_view):
        st.markdown("**Doctor-ready consultation note**")
        st.write(report.doctor_note)
        if report.clinician_questions:
            st.markdown("**Questions to ask your clinician**")
            for question in report.clinician_questions:
                st.write(f"• {question}")
        brief = build_visit_brief(profile, output, delta=delta)
        st.download_button(
            "Download Doctor Visit Brief (.md)",
            data=brief,
            file_name="ExtraCare_AI_Doctor_Visit_Brief.md",
            mime="text/markdown",
            key=f"{view_key}_doctor_brief",
        )


def _record_activity(mode: str, output: PipelineOutput, input_fp: str) -> None:
    if output.status != "ok" or output.report is None:
        return
    history = st.session_state.setdefault("extracare_activity_history", [])
    if any(entry.get("fingerprint") == input_fp for entry in history):
        return
    history.append(
        {
            "fingerprint": input_fp,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "mode": mode,
            "summary": output.extracted_summary,
            "verdict": output.report.verdict,
            "score": 100 - output.report.safety_score,
        }
    )
    del history[:-20]


def _record_lab_history(profile: PatientProfile, output: PipelineOutput, input_fp: str) -> None:
    if output.status != "ok" or output.extracted_lab is None or output.report is None:
        return
    history = st.session_state.setdefault("extracare_lab_history", [])
    lab_payload = output.extracted_lab.model_dump_json()
    lab_fp = hashlib.sha256((profile_fingerprint(profile) + "|" + lab_payload).encode("utf-8")).hexdigest()
    if any(entry.get("fingerprint") == lab_fp for entry in history):
        return
    history.append(
        {
            "fingerprint": lab_fp,
            "source_analysis_fingerprint": input_fp,
            "profile_fp": profile_fingerprint(profile),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "lab": output.extracted_lab.model_dump(),
            "verdict": output.report.verdict,
            "score": 100 - output.report.safety_score,
            "summary": output.extracted_summary,
        }
    )
    del history[:-10]


def latest_care_delta(profile: PatientProfile) -> Optional[CareDelta]:
    fingerprint = profile_fingerprint(profile)
    entries = [entry for entry in st.session_state.get("extracare_lab_history", []) if entry.get("profile_fp") == fingerprint]
    if len(entries) < 2:
        return None
    previous = ExtractedLabData(**entries[-2]["lab"])
    current = ExtractedLabData(**entries[-1]["lab"])
    return build_delta(previous, current)


def run_mode(
    mode: str,
    profile: PatientProfile,
    result_key: str,
    image_bytes: Optional[bytes] = None,
    product_image_bytes: Optional[bytes] = None,
    ingredients_text: Optional[str] = None,
    expected_product_type: Optional[str] = None,
) -> Optional[PipelineOutput]:
    st.session_state.pop(result_key, None)
    status = startup_status()
    if not status.get("groq") and mode != "text_check":
        st.error(
            "GROQ_API_KEY is missing or still contains the .env.example placeholder. "
            "Add a valid Groq key to .env and restart Streamlit."
        )
        return None

    fast_mode = st.session_state.get("analysis_speed_mode", "⚡ Fast") == "⚡ Fast"
    speed_tag = "fast" if fast_mode else "thorough"
    input_fp = analysis_fingerprint(
        mode + ":" + speed_tag,
        profile,
        image_bytes,
        product_image_bytes,
        ingredients_text,
        expected_product_type,
    )
    cache = st.session_state.setdefault("extracare_analysis_cache", {})

    if input_fp in cache:
        output = cache[input_fp]
        st.toast("Loaded instantly — same as your last check.")
    else:
        spinner_text = (
            "Reading your document and checking it against trusted sources..."
            if fast_mode
            else "Reading your document, searching for the latest information, and preparing a detailed answer..."
        )
        with st.spinner(spinner_text):
            try:
                output = controller_analyze(
                    mode,
                    profile,
                    image_bytes=image_bytes,
                    product_image_bytes=product_image_bytes,
                    ingredients_text=ingredients_text,
                    fast_mode=fast_mode,
                    expected_product_type=expected_product_type,
                )
            except Exception:
                st.error("Something went wrong while analyzing this. Please try again.")
                return None
        if output.status == "ok":
            cache[input_fp] = output
            while len(cache) > 20:
                del cache[next(iter(cache))]

    output.metadata["analysis_mode"] = speed_tag
    st.session_state[result_key] = output
    st.session_state[f"{result_key}_profile_fp"] = profile_fingerprint(profile)
    st.session_state[f"{result_key}_input_fp"] = input_fp
    _record_activity(mode, output, input_fp)
    if output.extracted_lab is not None:
        _record_lab_history(profile, output, input_fp)
    return output


def get_current_output(result_key: str, profile: PatientProfile) -> Optional[PipelineOutput]:
    output = st.session_state.get(result_key)
    if output is None:
        return None
    if st.session_state.get(f"{result_key}_profile_fp") != profile_fingerprint(profile):
        st.warning("Your health profile changed. The previous personalized result is hidden; re-run the analysis.")
        return None
    current_mode = "fast" if st.session_state.get("analysis_speed_mode", "⚡ Fast") == "⚡ Fast" else "thorough"
    if output.metadata.get("analysis_mode") != current_mode:
        st.info("Processing mode changed. Run the analysis again for this mode.")
        return None
    return output


def run_disease_protocol(disease_name: str, result_key: str) -> None:
    fast_mode = st.session_state.get("analysis_speed_mode", "⚡ Fast") == "⚡ Fast"
    cache = st.session_state.setdefault("extracare_protocol_cache", {})
    cache_key = f"{disease_name.strip().casefold()}|{'fast' if fast_mode else 'thorough'}"
    if cache_key in cache:
        st.session_state[result_key] = cache[cache_key]
        st.toast("Loaded protocol from this session's cache.")
        return

    with st.spinner("Building an evidence-grounded educational roadmap..."):
        protocol = controller_generate_protocol(disease_name, fast_mode=fast_mode)
    if not protocol.lifestyle_habits and not protocol.strict_restrictions and not protocol.diagnostic_tests:
        st.info("We don't have a ready-made guide for this condition. Switching to Thorough mode may give a broader overview if it's configured.")
    cache[cache_key] = protocol
    st.session_state[result_key] = protocol


def render_cross_match_page(category_label: str, sample_filename: str, profile: PatientProfile) -> None:
    key_prefix = category_label.lower()
    expected_product_type = "food" if category_label.casefold() == "food" else "skincare"
    st.markdown(
        f'<p class="mode-intro">Upload a diagnostic report and a {_esc(category_label.lower())} label. '
        "ExtraCare AI validates both input types before checking their interaction as one health context.</p>",
        unsafe_allow_html=True,
    )

    result_key = f"{key_prefix}_cross_match_result"
    lab_bytes_key = f"{key_prefix}_cross_lab_image_bytes"
    lab_id_key = f"{key_prefix}_cross_lab_upload_id"
    product_bytes_key = f"{key_prefix}_cross_product_image_bytes"
    product_id_key = f"{key_prefix}_cross_product_upload_id"

    left, right = st.columns(2)
    with left:
        st.markdown('<p class="section-label">Diagnostic report</p>', unsafe_allow_html=True)
        lab_uploaded = st.file_uploader(
            "Diagnostic report image/PDF",
            type=["png", "jpg", "jpeg", "pdf"],
            key=f"{key_prefix}_cross_lab_upload",
            label_visibility="collapsed",
        )
        if st.button("Use sample lab report", key=f"{key_prefix}_cross_lab_sample"):
            st.session_state[lab_bytes_key + "_source"] = "sample"
            st.session_state[lab_bytes_key] = load_sample_image("sample_blood_test.png")
            st.session_state.pop(result_key, None)
        sync_uploaded_document(lab_uploaded, lab_bytes_key, lab_id_key, result_key)
        if st.session_state.get(lab_bytes_key):
            render_document_preview(st.session_state[lab_bytes_key], caption="Diagnostic report", width=260)

    with right:
        st.markdown(f'<p class="section-label">{_esc(category_label)} label</p>', unsafe_allow_html=True)
        product_uploaded = st.file_uploader(
            "Product label image/PDF",
            type=["png", "jpg", "jpeg", "pdf"],
            key=f"{key_prefix}_cross_product_upload",
            label_visibility="collapsed",
        )
        if st.button(f"Use sample {category_label.lower()} label", key=f"{key_prefix}_cross_product_sample"):
            st.session_state[product_bytes_key + "_source"] = "sample"
            st.session_state[product_bytes_key] = load_sample_image(sample_filename)
            st.session_state.pop(result_key, None)
        sync_uploaded_document(product_uploaded, product_bytes_key, product_id_key, result_key)
        if st.session_state.get(product_bytes_key):
            render_document_preview(st.session_state[product_bytes_key], caption=f"{category_label} label", width=260)

    lab_bytes = st.session_state.get(lab_bytes_key)
    product_bytes = st.session_state.get(product_bytes_key)
    if (lab_bytes or product_bytes) and not (lab_bytes and product_bytes):
        st.caption(f"Add both a diagnostic report and a {category_label.lower()} label to continue.")

    if lab_bytes and product_bytes and st.button(
        f"Cross-match report & {category_label.lower()} product",
        key=f"{key_prefix}_cross_analyze",
        type="primary",
    ):
        run_mode(
            "cross_match",
            profile,
            result_key,
            image_bytes=lab_bytes,
            product_image_bytes=product_bytes,
            expected_product_type=expected_product_type,
        )

    output = get_current_output(result_key, profile)
    if output:
        render_report(
            output,
            profile,
            flags_heading="Problematic materials / interactions",
            view_key=f"{key_prefix}_cross",
        )


def render_disease_protocol(protocol: DiseaseProtocol) -> None:
    if protocol.summary:
        st.markdown(f'<div class="summary-block">{_esc(protocol.summary)}</div>', unsafe_allow_html=True)

    lifestyle, nutrition, monitoring = st.tabs(["Lifestyle", "Nutrition", "Monitoring roadmap"])
    with lifestyle:
        for habit in protocol.lifestyle_habits:
            st.write(f"• {habit}")

    with nutrition:
        left, right = st.columns(2)
        with left:
            st.markdown("**Strict restrictions / limits**")
            for item in protocol.strict_restrictions:
                st.markdown(f"**{item.item}**")
                st.write(item.reason)
                if item.target_or_limit:
                    st.caption(f"Evidence-backed target/limit: {item.target_or_limit}")
                if item.source:
                    st.caption(f"Source: {item.source}")
                st.divider()
        with right:
            st.markdown("**Recommended increases / supportive habits**")
            for item in protocol.recommended_increases:
                st.markdown(f"**{item.item}**")
                st.write(item.reason)
                if item.target_or_limit:
                    st.caption(f"Evidence-backed target: {item.target_or_limit}")
                if item.source:
                    st.caption(f"Source: {item.source}")
                st.divider()

    with monitoring:
        for test in protocol.diagnostic_tests:
            st.markdown(f"**{test.test_name}** · {test.interval}")
            st.write(test.reasoning)
            if test.source:
                st.caption(f"Source: {test.source}")
            st.divider()

    if protocol.evidence_sources:
        with st.expander("Evidence sources used"):
            for source in protocol.evidence_sources:
                st.write(f"• {source}")
    st.caption(
        "Backed by a live web search."
        if protocol.used_live_search
        else "Backed by our built-in knowledge base; live search wasn't needed or wasn't available."
    )


def render_health_timeline(profile: PatientProfile) -> None:
    st.info("Private-by-default prototype behavior: this timeline exists only in the current Streamlit session and is not written to a database.")

    if st.session_state.pop("extracare_memory_cleared_notice", False):
        st.success("Session health memory and cached analyses cleared.")

    activity = st.session_state.get("extracare_activity_history", [])
    labs = st.session_state.get("extracare_lab_history", [])
    left, right = st.columns(2)
    left.metric("Checks this session", len(activity))
    right.metric("Lab reports in timeline", len(labs))

    if st.button("Clear session health memory", type="secondary"):
        for key in (
            "extracare_activity_history",
            "extracare_lab_history",
            "extracare_analysis_cache",
            "extracare_protocol_cache",
        ):
            st.session_state.pop(key, None)
        for key in list(st.session_state):
            if (key.endswith(("_result", "_profile_fp", "_input_fp", "_image_bytes", "_upload_id", "_image_bytes_source", "_upload"))
                    or key in {"text_check_last_input", "protocol_last_disease", "text_check_input"}):
                st.session_state.pop(key, None)
        st.session_state["extracare_memory_cleared_notice"] = True
        st.rerun()

    if activity:
        st.markdown('<p class="section-label">Recent decisions</p>', unsafe_allow_html=True)
        rows = [
            {
                "Time": entry["timestamp"],
                "Mode": entry["mode"].replace("_", " ").title(),
                "Concern": entry["score"],
                "Context": entry["summary"][:120],
            }
            for entry in reversed(activity)
        ]
        st.dataframe(rows, hide_index=True, width="stretch")

    delta = latest_care_delta(profile)
    if delta:
        render_care_delta(delta)
    elif labs:
        st.caption("Analyze one more lab report with the same health profile to unlock CareDelta.")
    else:
        st.caption("Analyze a lab report to start your session-only health timeline.")


def render_footer() -> None:
    st.markdown(
        """
        <div class="disclaimer-footer">
            <strong>ExtraCare AI</strong> is an educational course-project prototype, not a medical device.
            It does not diagnose, prescribe, or replace a licensed clinician. The bundled knowledge base is
            limited; numeric thresholds are shown only when retrieved evidence supports them. When evidence
            is insufficient, the system is designed to qualify or abstain rather than fabricate precision.
            Emergency symptoms require real-world medical care, not this app.
        </div>
        """,
        unsafe_allow_html=True,
    )
