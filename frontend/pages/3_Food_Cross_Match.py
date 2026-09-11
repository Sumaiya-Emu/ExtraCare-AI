"""Food + diagnostic report cross-match."""
import streamlit as st
from ui_common import load_css, render_cross_match_page, render_footer, render_page_header, render_profile_sidebar

st.set_page_config(page_title="ExtraCare AI — Food Cross-Match", page_icon="🥗", layout="wide")
load_css()
render_page_header("Food Cross-Match", "One question: does this food/product matter more because of what is in my report?")
profile = render_profile_sidebar()
render_cross_match_page("Food", "sample_food_label.png", profile)
render_footer()
