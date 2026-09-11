"""ExtraCare AI home page."""
import streamlit as st

from ui_common import load_css, render_footer, render_profile_sidebar

st.set_page_config(page_title="ExtraCare AI", page_icon="🧬", layout="wide")
load_css()

st.markdown(
    """
    <div class="hero">
        <p class="hero__eyebrow">ONE PROFILE → ONE INTELLIGENCE LAYER → MULTIPLE HEALTH DECISIONS</p>
        <p class="hero__title">Your personal health context engine.</p>
        <p class="hero__subtitle">
            ExtraCare AI connects diagnostic reports, health conditions, medications, product labels,
            previous results in the current session, and evidence. It does not just explain a lab value or ingredient in
            isolation — it helps you understand what the combination means, what changed, and what to ask next.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

profile = render_profile_sidebar()

c1, c2, c3 = st.columns(3)
c1.metric(
    "One profile",
    "Used everywhere",
    help="Fill in your health profile once in the sidebar — every tool on this site reuses it.",
)
c2.metric(
    "Not sure?",
    "We say so",
    help="If your document or details aren't clear enough to analyze safely, we say so instead of guessing.",
)
c3.metric(
    "Every answer",
    "Real sources",
    help="Results are checked against real medical references and, when needed, current search results — not just AI guesses.",
)

st.markdown('<p class="section-label">What do you want to do?</p>', unsafe_allow_html=True)

modes = [
    ("mode-card--lab", "🩺", "Understand my labs", "Blood, urinalysis/UACR, or a written X-Ray/Ultrasound/MRI/CT report. Includes CareDelta when you analyze a later report.", "pages/1_Lab_Decoder.py"),
    ("mode-card--product", "🛒", "Check a product", "Read a food, medicine, supplement, or skincare label; classify complete-avoidance vs dose-dependent restrictions.", "pages/2_Product_Sentinel.py"),
    ("mode-card--cross", "🥗", "Cross-match food + labs", "See whether a food/product concern becomes more important because of your actual diagnostic findings.", "pages/3_Food_Cross_Match.py"),
    ("mode-card--cross", "🧴", "Cross-match skincare + labs", "Combine diagnostic context with cosmetic ingredients, including pregnancy and condition-specific cautions.", "pages/4_Skincare_Cross_Match.py"),
    ("mode-card--text", "⚡", "Quick ingredient check", "Already know the ingredient name? Skip the photo and type it in directly — same checks, faster.", "pages/5_Quick_Ingredient_Check.py"),
    ("mode-card--hub", "📋", "Disease care protocol", "General evidence-grounded lifestyle, nutrition, and monitoring roadmap for a disease/condition.", "pages/6_Disease_Care_Hub.py"),
    ("mode-card--timeline", "📈", "Track what changed", "Session-only health timeline, previous checks, and CareDelta — no persistent database by default.", "pages/7_My_Health_Timeline.py"),
]

columns = st.columns(2)
for i, (css_class, icon, title, desc, target) in enumerate(modes):
    with columns[i % 2]:
        st.markdown(
            f"""
            <div class="mode-card {css_class}">
                <div class="mode-card__icon">{icon}</div>
                <p class="mode-card__title">{title}</p>
                <p class="mode-card__desc">{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link(target, label=f"Open {title}")

st.markdown(
    """
    <div class="platform-story">
        <strong>Why this is one system, not seven disconnected tools</strong><br>
        Every analysis starts from the same Core Health Profile and ends in the same structured evidence model.
        CareGraph, Confidence Gate, specialist routing, CareSwap, and the Doctor Visit Brief reuse that output
        instead of making extra AI calls just for presentation.
    </div>
    """,
    unsafe_allow_html=True,
)

render_footer()
