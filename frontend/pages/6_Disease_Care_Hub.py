"""Disease Care & Protocol Hub."""
import streamlit as st

from ui_common import (
    CONDITION_OPTIONS,
    load_css,
    render_disease_protocol,
    render_footer,
    render_page_header,
    render_profile_sidebar,
    run_disease_protocol,
)

st.set_page_config(page_title="ExtraCare AI — Disease Care & Protocol Hub", page_icon="📋", layout="wide")
load_css()
render_page_header("Disease Care & Protocol Hub", "General evidence-grounded lifestyle, nutrition, and monitoring roadmap.")
profile = render_profile_sidebar()

st.warning("This hub gives general educational condition guidance. It is not a personalized treatment plan; use the other modes for profile-specific product/report analysis.")

quick_pick_options = list(dict.fromkeys(profile.chronic_conditions + CONDITION_OPTIONS))
quick_pick = st.selectbox("Search/select a condition", ["-- choose --"] + quick_pick_options, key="protocol_quick_pick")
typed_disease = st.text_input(
    "Or type any disease/condition",
    placeholder="e.g. Migraine, Osteoporosis, Iron-Deficiency Anemia",
    key="protocol_typed_input",
)
disease_name = typed_disease.strip() or (quick_pick if quick_pick != "-- choose --" else "")

if st.session_state.get("protocol_last_disease") != disease_name or st.session_state.get("protocol_last_mode") != st.session_state.get("analysis_speed_mode"):
    st.session_state.pop("protocol_result", None)

if disease_name and st.button("Generate protocol", key="protocol_generate", type="primary"):
    run_disease_protocol(disease_name, result_key="protocol_result")
    st.session_state["protocol_last_disease"] = disease_name
    st.session_state["protocol_last_mode"] = st.session_state.get("analysis_speed_mode")

if "protocol_result" in st.session_state:
    protocol = st.session_state["protocol_result"]
    st.markdown(f"### Protocol for: {protocol.disease_name}")
    render_disease_protocol(protocol)

render_footer()
