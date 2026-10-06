"""Cleanup tracking: an authorised user updates status, uploads before/after photos
and runs the visual cleanup verification."""
import os

import streamlit as st
from dotenv import load_dotenv

from src.ui import setup_page, page_header
from src.reports import (BASE_DIR, STATUSES, load_reports, update_status,
                         save_cleanup_photo, find_cleanup_photo)
from src.pollution_detection import visual_cleanup_verification

setup_page("Cleanup Tracking", "🧹")
page_header("🧹 Cleanup Tracking",
            "Update complaint status and upload before/after photographs.")

# The admin password is stored in the .env file (ADMIN_PASSWORD=...)
load_dotenv(BASE_DIR / ".env")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# ---------- Simple admin login ----------
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if not st.session_state.is_admin:
    st.write("This page is for authorised users only.")
    pwd = st.text_input("Admin password", type="password")
    if st.button("Log in as admin"):
        if ADMIN_PASSWORD and pwd == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()          # nothing below is shown until logged in

# ---------- Choose a report ----------
df = load_reports()
if df.empty:
    st.info("No reports yet. Submit one on the Report Pollution page.")
    st.stop()

options = {f"{r['Report ID']}  |  {r['Lake Name']}  |  {r['Complaint Status']}": r["Report ID"]
           for _, r in df.iterrows()}
report_id = options[st.selectbox("Select a report", list(options.keys()))]
row = df[df["Report ID"] == report_id].iloc[0]

# ---------- Update status ----------
st.subheader("Complaint status")
current = row["Complaint Status"]
index = STATUSES.index(current) if current in STATUSES else 0
new_status = st.selectbox("New status", STATUSES, index=index)
if st.button("Update status"):
    update_status(report_id, new_status)
    st.success(f"Status of {report_id} changed to '{new_status}'.")
    st.rerun()

# ---------- Before / after photos ----------
st.subheader("Before and after photographs")
col_b, col_a = st.columns(2)
for col, kind in ((col_b, "before"), (col_a, "after")):
    with col:
        st.markdown(f"**{kind.capitalize()} cleanup**")
        up = st.file_uploader(f"Upload {kind} photo", type=["jpg", "jpeg", "png"],
                              key=f"{kind}_{report_id}")
        if up is not None and st.button(f"Save {kind} photo", key=f"save_{kind}_{report_id}"):
            save_cleanup_photo(up, report_id, kind)
            st.rerun()
        photo = find_cleanup_photo(report_id, kind)
        if photo:
            st.image(str(photo), width="stretch")
        else:
            st.caption("No photo saved yet.")

# ---------- Visual cleanup verification ----------
st.subheader("Visual cleanup verification")
before_p = find_cleanup_photo(report_id, "before")
after_p = find_cleanup_photo(report_id, "after")

if before_p and after_p:
    ignore_top = st.slider("Ignore the top part of the photos (sky), %", 0, 50, 20,
                           key="cleanup_ignore")
    if st.button("Compare before and after"):
        v = visual_cleanup_verification(before_p, after_p, ignore_top)
        m1, m2, m3 = st.columns(3)
        m1.metric("Before visible waste", f"{v['before_pct']}%")
        m2.metric("After visible waste", f"{v['after_pct']}%")
        m3.metric("Estimated visual reduction", f"{v['reduction_pct']}%")
        i1, i2 = st.columns(2)
        i1.image(v["before_overlay"], caption="Before (flagged in red)", width="stretch")
        i2.image(v["after_overlay"], caption="After (flagged in red)", width="stretch")
else:
    st.caption("Save both a before photo and an after photo to enable the comparison.")

st.info("This is a visual comparison only. It is not proof of restored water quality. "
        "For a fair comparison, take both photos from the same spot and angle.")

if st.button("Log out of admin"):
    st.session_state.is_admin = False
    st.rerun()