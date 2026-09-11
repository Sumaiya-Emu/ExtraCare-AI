"""Product Sentinel: product label + profile-aware restriction classification."""
import streamlit as st

from ui_common import (
    get_current_output,
    render_document_preview,
    sync_uploaded_document,
    load_css,
    load_sample_image,
    render_footer,
    render_page_header,
    render_profile_sidebar,
    render_report,
    run_mode,
)

st.set_page_config(page_title="ExtraCare AI — Product Sentinel", page_icon="🛒", layout="wide")
load_css()
render_page_header("Product Sentinel", "Complete avoidance vs dose-dependent caution — grounded in your profile and evidence.")
profile = render_profile_sidebar()

if not profile.chronic_conditions and not profile.is_pregnant:
    st.info("No condition is selected. ExtraCare AI will still show evidence-backed general conditions that require complete avoidance versus moderation when relevant.")

st.markdown(
    '<p class="mode-intro">Upload a food, medicine/supplement, or skincare label. We read the ingredient list, check it against safety recalls and trusted sources, and tell you what to avoid or watch for based on your profile.</p>',
    unsafe_allow_html=True,
)
st.caption("Medicine/supplement labels are treated as ingredient/excipient context only; ExtraCare AI is not a comprehensive drug-interaction database.")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded = st.file_uploader("Product label image or PDF", type=["png", "jpg", "jpeg", "pdf"], key="product_upload")
with col2:
    if st.button("Use sample food label", key="product_sample_food"):
        st.session_state["product_image_bytes"] = load_sample_image("sample_food_label.png")
        st.session_state["product_image_bytes_source"] = "sample"
        st.session_state.pop("product_report_result", None)
    if st.button("Use sample skincare label", key="product_sample_skincare"):
        st.session_state["product_image_bytes"] = load_sample_image("sample_skincare_label.png")
        st.session_state["product_image_bytes_source"] = "sample"
        st.session_state.pop("product_report_result", None)

sync_uploaded_document(uploaded, "product_image_bytes", "product_upload_id", "product_report_result")

image_bytes = st.session_state.get("product_image_bytes")
if image_bytes:
    render_document_preview(image_bytes, caption="Product label preview", width=340)

if image_bytes and st.button("Analyze product", key="product_analyze", type="primary"):
    run_mode("product", profile, result_key="product_report_result", image_bytes=image_bytes)

output = get_current_output("product_report_result", profile)
if output:
    render_report(output, profile, concern_display=True, flags_heading="Flagged ingredients / restrictions", view_key="product")

render_footer()
