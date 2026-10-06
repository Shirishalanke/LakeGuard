"""Shared CSS and small UI helpers. CSS is injected once from app.py."""
import streamlit as st

CSS = """
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {display: none;}
#MainMenu, footer, .stDeployButton, [data-testid="stAppDeployButton"] {visibility: hidden;}
.block-container {padding-top: 1rem; max-width: 1150px;}

/* Official-style top strip (saffron / white / green) */
.flagbar {height: 6px; border-radius: 3px;
  background: linear-gradient(90deg,#ff9933 33%,#ffffff 33% 66%,#138808 66%);}
.portal-title {display:flex; align-items:center; gap:.9rem; padding:.7rem 0 .4rem 0;}
.portal-title .logo {font-size:2.4rem;}
.portal-title h2 {margin:0; font-size:1.55rem; color:#1e3a8a;}
.portal-title p {margin:0; font-size:.85rem; opacity:.75;}

.hero {background: linear-gradient(135deg,#0ea5e9,#2563eb 60%,#1e3a8a);
  padding:1.6rem 2rem; border-radius:14px; color:white; margin-bottom:1.3rem;}
.hero h1 {margin:0; font-size:1.9rem; color:white;}
.hero p {margin:.3rem 0 0 0; opacity:.92; color:white;}

.card {background: rgba(148,163,184,.10); border:1px solid rgba(148,163,184,.25);
  border-radius:12px; padding:1rem 1.2rem; height:100%;}
.card h4 {margin:0 0 .4rem 0;}
div[data-testid="stMetric"] {background: rgba(148,163,184,.10);
  border:1px solid rgba(148,163,184,.25); border-radius:12px; padding:.8rem 1rem;}

.stButton > button, div[data-testid="stFormSubmitButton"] > button {
  background:#2563eb; color:white; border:none; border-radius:8px; font-weight:600;}
.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
  background:#1d4ed8; color:white;}

.site-footer {text-align:center; font-size:.8rem; opacity:.65; padding:1.5rem 0 .5rem 0;}

/* ---------- Login page ---------- */
.login-left {
  background: linear-gradient(160deg,#0ea5e9 0%,#2563eb 55%,#1e3a8a 100%);
  color:white; border-radius:18px; padding:2.2rem 2rem; min-height:430px;
  box-shadow: 0 10px 30px rgba(37,99,235,.35);
}
.login-left h2 {color:white; margin:0 0 .4rem 0; font-size:1.8rem;}
.login-left p {color:white; opacity:.92; margin:0 0 1.2rem 0;}
.login-left ul {list-style:none; padding:0; margin:0;}
.login-left li {padding:.55rem .8rem; margin-bottom:.55rem; border-radius:10px;
  background: rgba(255,255,255,.14); font-size:.95rem;}

/* The bordered container that holds the login form */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius:18px; padding:.6rem .8rem;
  box-shadow: 0 6px 24px rgba(0,0,0,.12);
}
/* Rounded input boxes with a blue focus ring */
div[data-baseweb="input"], div[data-baseweb="base-input"] {border-radius:10px !important;}
div[data-baseweb="input"]:focus-within {box-shadow: 0 0 0 2px rgba(37,99,235,.55);}
/* Tabs */
button[data-baseweb="tab"] {font-weight:600; font-size:1rem;}
/* Make login buttons full width */
[data-testid="stVerticalBlockBorderWrapper"] .stButton > button {width:100%; padding:.6rem 0;}
</style>
"""


def setup_page(title: str = "", icon: str = ""):
    """Pages call this; the CSS is already loaded by app.py, so nothing is needed.
    (st.set_page_config is called ONCE in app.py.)"""
    return None


def page_header(title: str, subtitle: str = ""):
    """Blue banner at the top of a page."""
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
                unsafe_allow_html=True)


def portal_title():
    """Top strip and portal name shown on every page."""
    st.markdown(
        '<div class="flagbar"></div>'
        '<div class="portal-title"><div class="logo">🌊</div><div>'
        '<h2>LakeGuard AI</h2>'
        '<p>Lake Pollution Reporting &amp; Cleanup Portal &middot; Hyderabad</p>'
        '</div></div>', unsafe_allow_html=True)