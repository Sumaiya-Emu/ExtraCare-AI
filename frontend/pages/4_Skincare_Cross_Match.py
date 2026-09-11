"""Skincare + diagnostic report cross-match."""
import streamlit as st
from ui_common import load_css, render_cross_match_page, render_footer, render_page_header, render_profile_sidebar

st.set_page_config(page_title="ExtraCare AI — Skincare Cross-Match", page_icon="🧴", layout="wide")
load_css()
render_page_header("Skincare Cross-Match", "Connect a written diagnostic report with skincare/cosmetic ingredients in the same health context.")
profile = render_profile_sidebar()
render_cross_match_page("Skincare", "sample_skincare_label.png", profile)
render_footer()
