"""Session-only Personal Health Memory and CareDelta dashboard."""
import streamlit as st

from ui_common import load_css, render_footer, render_health_timeline, render_page_header, render_profile_sidebar

st.set_page_config(page_title="ExtraCare AI — My Health Timeline", page_icon="📈", layout="wide")
load_css()
render_page_header("My Health Timeline", "See what you checked and what changed — stored only in this browser session by default.")
profile = render_profile_sidebar()
render_health_timeline(profile)
render_footer()
