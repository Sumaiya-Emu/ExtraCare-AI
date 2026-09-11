"""Quick Ingredient Check — fast typed path or product-label OCR path."""
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

st.set_page_config(page_title="ExtraCare AI — Quick Ingredient Check", page_icon="⚡", layout="wide")
load_css()
render_page_header("Quick Ingredient Check", "Type what you already know for the fastest path — or upload a label when you do not.")
profile = render_profile_sidebar()

if not profile.chronic_conditions and not profile.is_pregnant:
    st.info("No condition is selected. General evidence-backed complete-avoidance vs moderation contexts will be shown when available.")

tab_type, tab_upload = st.tabs(["⚡ Type it — fastest", "📷 Upload a label"])

with tab_type:
    ingredients_text = st.text_area(
        "Ingredient(s)",
        placeholder="e.g. Gluten, Caffeine, Sodium Chloride",
        key="text_check_input",
        height=100,
    )
    current_text = ingredients_text.strip()
    if st.session_state.get("text_check_last_input") != current_text:
        st.session_state.pop("quick_text_result", None)
    if current_text and st.button("Check ingredient(s)", key="text_check_analyze", type="primary"):
        run_mode("text_check", profile, result_key="quick_text_result", ingredients_text=current_text)
        st.session_state["text_check_last_input"] = current_text

    output = get_current_output("quick_text_result", profile)
    if output:
        render_report(output, profile, concern_display=True, flags_heading="Flagged ingredients", view_key="quick_text")

with tab_upload:
    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded = st.file_uploader("Product label image/PDF", type=["png", "jpg", "jpeg", "pdf"], key="quick_upload")
    with col2:
        if st.button("Sample food label", key="quick_sample_food"):
            st.session_state["quick_image_bytes"] = load_sample_image("sample_food_label.png")
            st.session_state["quick_image_bytes_source"] = "sample"
            st.session_state.pop("quick_image_result", None)
        if st.button("Sample skincare label", key="quick_sample_skincare"):
            st.session_state["quick_image_bytes"] = load_sample_image("sample_skincare_label.png")
            st.session_state["quick_image_bytes_source"] = "sample"
            st.session_state.pop("quick_image_result", None)

    sync_uploaded_document(uploaded, "quick_image_bytes", "quick_upload_id", "quick_image_result")

    image_bytes = st.session_state.get("quick_image_bytes")
    if image_bytes:
        render_document_preview(image_bytes, caption="Label preview", width=300)
    if image_bytes and st.button("Analyze label", key="quick_image_analyze", type="primary"):
        run_mode("product", profile, result_key="quick_image_result", image_bytes=image_bytes)

    output = get_current_output("quick_image_result", profile)
    if output:
        render_report(output, profile, concern_display=True, flags_heading="Flagged ingredients", view_key="quick_image")

render_footer()
