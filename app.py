"""LakeGuard AI - main file. Run with: streamlit run app.py
Email + OTP login first; after login the portal opens with top navigation."""
import streamlit as st

from src.ui import CSS, portal_title
from src.auth import valid_email, find_by_email, validate_registration, register_user
from src.otp import create_otp, verify_otp

st.set_page_config(page_title="LakeGuard AI", page_icon="🌊", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
portal_title()

# Light-colour styling used ONLY on the login / register / code screens
LOGIN_LIGHT_CSS = """
<style>
[data-testid="stApp"] {background: linear-gradient(160deg,#e8f4ff 0%,#f7fbff 50%,#dff0ff 100%) !important;}
[data-testid="stHeader"] {background: transparent !important;}
.portal-title h2 {color:#1e3a8a !important;}
.portal-title p, .site-footer {color:#334155 !important; opacity:1 !important;}

/* White card, and dark readable text inside it */
.st-key-login_card {background:#ffffff !important; border:1px solid #cfe3f7 !important;
  border-radius:18px; box-shadow:0 8px 28px rgba(37,99,235,.15);}
.st-key-login_card h1, .st-key-login_card h2, .st-key-login_card h3,
.st-key-login_card label, .st-key-login_card label p,
.st-key-login_card [data-testid="stWidgetLabel"] p,
.st-key-login_card [data-testid="stCaptionContainer"] {color:#0f172a !important;}

/* ---- Input boxes: light background, dark text ---- */
.st-key-login_card [data-testid="stTextInputRootElement"],
.st-key-login_card div[data-baseweb="input"],
.st-key-login_card div[data-baseweb="base-input"],
.st-key-login_card input {
  background:#eef5fd !important; background-color:#eef5fd !important;
  color:#0f172a !important; -webkit-text-fill-color:#0f172a !important;
  caret-color:#0f172a !important;
}
.st-key-login_card [data-testid="stTextInputRootElement"],
.st-key-login_card div[data-baseweb="input"] {
  border:1.5px solid #9fc2e8 !important; border-radius:10px !important;
}
.st-key-login_card [data-testid="stTextInputRootElement"]:focus-within {
  border-color:#2563eb !important; box-shadow:0 0 0 2px rgba(37,99,235,.25) !important;
}
.st-key-login_card input::placeholder {color:#64748b !important; -webkit-text-fill-color:#64748b !important;}

/* ---- Tabs: both fully red ---- */
.st-key-login_card [data-baseweb="tab-list"] {gap:.7rem !important; border-bottom:none !important;}
.st-key-login_card [data-baseweb="tab-highlight"],
.st-key-login_card [data-baseweb="tab-border"] {display:none !important;}

/* Every tab: white box, red outline, red text, never faded */
.st-key-login_card button[data-baseweb="tab"],
.st-key-login_card [data-testid="stTab"],
.st-key-login_card [role="tab"] {
  background:#ffffff !important; border:2px solid #dc2626 !important;
  border-radius:10px !important; padding:.45rem 1.6rem !important; opacity:1 !important;
}
.st-key-login_card [role="tab"],
.st-key-login_card [role="tab"] *,
.st-key-login_card [data-testid="stTab"] * {
  color:#dc2626 !important; opacity:1 !important;
  font-weight:700 !important; font-size:1.05rem !important;
}

/* Selected tab: solid red with white text */
.st-key-login_card [role="tab"][aria-selected="true"] {background:#dc2626 !important;}
.st-key-login_card [role="tab"][aria-selected="true"],
.st-key-login_card [role="tab"][aria-selected="true"] * {color:#ffffff !important;}

/* ---- Buttons ---- */
.st-key-login_card .stButton > button {background:#2563eb !important; border:none !important;}
.st-key-login_card .stButton > button p {color:#ffffff !important;}

/* ---- Spinner ("Sending code...") and messages ---- */
.st-key-login_card [data-testid="stSpinner"],
.st-key-login_card [data-testid="stSpinner"] *,
.st-key-login_card .stSpinner, .st-key-login_card .stSpinner * {color:#0f172a !important; opacity:1 !important;}
.st-key-login_card [data-testid="stAlert"] {background:#eef5fd !important; border:1px solid #cfe3f7 !important;}
.st-key-login_card [data-testid="stAlert"] p, .st-key-login_card [data-testid="stAlert"] * {color:#0f172a !important;}

/* Keep the blue welcome panel text white */
.login-left, .login-left * {color:#ffffff !important;}
</style>
"""

LOGIN_LEFT = """
<div class="login-left">
  <h2>Welcome to LakeGuard AI</h2>
  <p>Help protect Hyderabad's lakes. Report visible pollution and follow the cleanup.</p>
  <ul>
    <li>📸 Report pollution with a photo and location</li>
    <li>🔍 Automated visual assessment of the photo</li>
    <li>🗺️ See pollution hotspots on a map</li>
    <li>🔎 Find lakes near any place and how far they are</li>
    <li>📨 Prepare a complaint for the official GHMC channel</li>
    <li>🧹 Track cleanup progress with before/after photos</li>
  </ul>
</div>
"""


def start_otp(email: str, pending: dict):
    """Create + send an OTP, remember what we are verifying, and show the code screen."""
    with st.spinner("Sending code, please wait..."):
        state, msg = create_otp(email)
    if state is None:
        st.error(msg, icon="⚠️")
        return
    st.session_state.otp = state
    st.session_state.pending = pending
    st.rerun()


def otp_step():
    """Screen where the user types the code they received."""
    state, pending = st.session_state.otp, st.session_state.pending
    st.subheader("🔑 Enter the verification code")
    st.info(state["message"], icon="✉️")
    if state["demo_code"]:
        st.warning(f"DEMO MODE (not secure): your code is **{state['demo_code']}**", icon="⚠️")

    code = st.text_input("6-digit code", max_chars=6, key="otp_input")
    if st.button("Verify", key="verify_btn"):
        ok, msg = verify_otp(state, code)
        if not ok:
            st.error(msg, icon="⚠️")
        else:
            if pending["mode"] == "register":
                register_user(pending["name"], state["email"])
            st.session_state.user = find_by_email(state["email"])
            del st.session_state["otp"], st.session_state["pending"]
            st.rerun()                     # Home page opens
    c1, c2 = st.columns(2)
    if c1.button("Resend code", key="resend_btn"):
        start_otp(state["email"], pending)
    if c2.button("Back", key="back_btn"):
        del st.session_state["otp"], st.session_state["pending"]
        st.rerun()


def login_forms():
    """Login and Register tabs."""
    st.subheader("Citizen login")
    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        email = st.text_input("Email", key="l_email", placeholder="you@example.com")
        if st.button("Send OTP", key="login_send"):
            if not valid_email(email):
                st.error("Enter a valid email address.", icon="⚠️")
            elif not find_by_email(email):
                st.error("No account found with this email. Please register first.", icon="⚠️")
            else:
                start_otp(email.strip().lower(), {"mode": "login"})

    with tab_register:
        name = st.text_input("Full name", key="r_name")
        email_r = st.text_input("Email", key="r_email", placeholder="you@example.com")
        if st.button("Register and send OTP", key="reg_send"):
            ok, msg = validate_registration(name, email_r)
            if not ok:
                st.error(msg, icon="⚠️")
            else:
                start_otp(email_r.strip().lower(), {"mode": "register", "name": name})


def login_page():
    """Two columns: blue welcome panel on the left, light form card on the right."""
    st.markdown(LOGIN_LIGHT_CSS, unsafe_allow_html=True)
    left, right = st.columns([5, 6], gap="large")
    with left:
        st.markdown(LOGIN_LEFT, unsafe_allow_html=True)
    with right:
        with st.container(border=True, key="login_card"):
            if "otp" in st.session_state:
                otp_step()
            else:
                login_forms()


if "user" not in st.session_state:
    nav = st.navigation([st.Page(login_page, title="Login", icon="🔐")], position="hidden")
else:
    pages = [
        st.Page("pages/home.py", title="Home", icon="🏠", default=True),
        st.Page("pages/citizen_report.py", title="Report Pollution", icon="📝"),
        st.Page("pages/hotspot_map.py", title="Hotspot Map", icon="🗺️"),
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
        st.Page("pages/water_quality.py", title="Water Quality", icon="💧"),
        st.Page("pages/ghmc_complaint.py", title="GHMC Complaint", icon="📨"),
        st.Page("pages/cleanup.py", title="Cleanup Tracking", icon="🧹"),
    ]
    nav = st.navigation(pages, position="top")

    u = st.session_state.user
    c1, c2 = st.columns([6, 1])
    c1.caption(f"👤 {u['Name']}  |  ✉️ {u['Email']}")
    if c2.button("Logout"):
        del st.session_state["user"]
        st.rerun()

nav.run()

st.markdown('<div class="site-footer">LakeGuard AI is an independent citizen platform and '
            'is not operated by GHMC. Visual assessments are automated and are not '
            'laboratory water-quality measurements.</div>', unsafe_allow_html=True)