"""Prepare a complaint and take the user to the OFFICIAL GHMC grievance channel."""
import streamlit as st

from src.ui import page_header
from src.reports import BASE_DIR, load_reports, update_status
from src.complaint import build_complaint

page_header("📨 GHMC Complaint",
            "Prepare a complaint here, then submit it on the official GHMC channel.")

st.warning("**LakeGuard is not the GHMC grievance system.** It does not submit anything "
           "to GHMC. Prepare your complaint here, then file it on GHMC's official website "
           "or helpline to get an official complaint reference number.")

df = load_reports()
if df.empty:
    st.info("No reports yet. Submit one on the Report Pollution page first.")
    st.stop()

options = {f"{r['Report ID']} | {r['Lake Name']}": r["Report ID"] for _, r in df.iterrows()}
rid = options[st.selectbox("Choose a report", list(options.keys()))]
row = df[df["Report ID"] == rid].iloc[0]

st.subheader("1. Review your complaint")
text = st.text_area("Complaint text (you can edit it)", build_complaint(row), height=380)

c1, c2 = st.columns(2)
c1.download_button("⬇️ Download complaint (.txt)", text, file_name=f"{rid}_complaint.txt")
photo = BASE_DIR / str(row["Image Path"])
if photo.exists():
    c2.download_button("⬇️ Download photo evidence", photo.read_bytes(), file_name=photo.name)

if st.button("Mark as 'Complaint prepared'"):
    update_status(rid, "Complaint prepared")
    st.success("Status updated.")

st.subheader("2. File it on the official GHMC channel")
st.link_button("Open official GHMC website (ghmc.gov.in)", "https://www.ghmc.gov.in")
st.markdown(
    "On the GHMC site, use the **Grievance** option for citizens (or the MyGHMC app), "
    "paste your complaint text, attach the photo, and note the reference number GHMC "
    "gives you.\n\n"
    "Helplines reported publicly: **155304** and **040-21111111**. "
    "Please confirm the current numbers and steps on ghmc.gov.in, as they can change.")

st.subheader("3. After you have filed it")
if st.button("I have submitted it on the GHMC portal"):
    update_status(rid, "Complaint submitted")
    st.success("Status updated to 'Complaint submitted'.")