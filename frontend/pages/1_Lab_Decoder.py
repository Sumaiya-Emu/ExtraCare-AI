"""Diagnostic report decoder: blood, urinalysis and written radiology reports."""
import streamlit as st

from ui_common import (
    get_current_output,
    render_document_preview,
    sync_uploaded_document,
    latest_care_delta,
    load_css,
    load_sample_image,
    render_footer,
    render_page_header,
    render_profile_sidebar,
    render_report,
    run_mode,
)

st.set_page_config(page_title="ExtraCare AI — Lab Decoder", page_icon="🩺", layout="wide")
load_css()
render_page_header("Lab Decoder", "Blood, urinalysis/UACR, and written radiology reports — interpreted in your health context.")
profile = render_profile_sidebar()

st.markdown(
    """
    <div class="support-strip">
        🩸 Blood/CBC &nbsp; · &nbsp; 🧪 Urinalysis/UACR &nbsp; · &nbsp; 🩻 X-Ray report &nbsp; · &nbsp;
        🔊 Ultrasound report &nbsp; · &nbsp; 🧠 MRI/CT report
    </div>
    """,
    unsafe_allow_html=True,
)
st.info("For radiology, upload the written Findings / Impression report. Raw DICOM films are not interpreted.")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded = st.file_uploader("Diagnostic report image or PDF", type=["png", "jpg", "jpeg", "pdf"], key="lab_upload")
with col2:
    if st.button("Sample blood panel", key="lab_sample"):
        st.session_state["lab_image_bytes"] = load_sample_image("sample_blood_test.png")
        st.session_state["lab_image_bytes_source"] = "sample"
        st.session_state.pop("lab_report_result", None)
    if st.button("Sample follow-up panel", key="lab_sample_followup"):
        st.session_state["lab_image_bytes"] = load_sample_image("sample_blood_test_followup.png")
        st.session_state["lab_image_bytes_source"] = "sample"
        st.session_state.pop("lab_report_result", None)
    if st.button("Sample urinalysis/UACR", key="lab_sample_urine"):
        st.session_state["lab_image_bytes"] = load_sample_image("sample_urinalysis.png")
        st.session_state["lab_image_bytes_source"] = "sample"
        st.session_state.pop("lab_report_result", None)
    if st.button("Sample radiology report", key="lab_sample_radiology"):
        st.session_state["lab_image_bytes"] = load_sample_image("sample_radiology_report.png")
        st.session_state["lab_image_bytes_source"] = "sample"
        st.session_state.pop("lab_report_result", None)

sync_uploaded_document(uploaded, "lab_image_bytes", "lab_upload_id", "lab_report_result")

image_bytes = st.session_state.get("lab_image_bytes")
if image_bytes:
    render_document_preview(image_bytes, caption="First-page preview (multi-page PDFs are analyzed up to the configured page cap)", width=340)

if image_bytes and st.button("Analyze diagnostic report", key="lab_analyze", type="primary"):
    run_mode("lab", profile, result_key="lab_report_result", image_bytes=image_bytes)

output = get_current_output("lab_report_result", profile)
if output:
    render_report(
        output,
        profile,
        view_key="lab",
        delta=latest_care_delta(profile),
    )
    if latest_care_delta(profile) is None and output.status == "ok":
        st.caption("CareDelta unlocks after you analyze a second report with the same health profile in this session.")

render_footer()
