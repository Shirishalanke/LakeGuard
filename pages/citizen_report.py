"""Report Pollution page: submit a report (with automated visual assessment)
and view all reports."""
from datetime import datetime

import streamlit as st
from PIL import Image

from src.ui import setup_page, page_header
from src.reports import (BASE_DIR, generate_report_id, save_image, save_report,
                         load_reports, show_report)
from src.pollution_detection import analyse_image, DISCLAIMER

setup_page("Report Pollution", "📝")
page_header("📝 Report Pollution", "Upload a lake photograph and describe what you see.")

tab_submit, tab_all = st.tabs(["Submit a report", "All reports"])

with tab_submit:
    with st.form("report_form"):
        lake_name = st.text_input("Lake name *", placeholder="e.g. Hussain Sagar")

        c1, c2 = st.columns(2)
        latitude = c1.number_input("Latitude *", value=17.385000, format="%.6f",
                                   min_value=-90.0, max_value=90.0)
        longitude = c2.number_input("Longitude *", value=78.486700, format="%.6f",
                                    min_value=-180.0, max_value=180.0)

        c3, c4 = st.columns(2)
        obs_date = c3.date_input("Date observed", value=datetime.now().date())
        obs_time = c4.time_input("Time observed",
                                 value=datetime.now().time().replace(microsecond=0))

        description = st.text_area("Describe the problem *",
                                   placeholder="e.g. Plastic bottles floating near the north bund")
        photo = st.file_uploader("Upload lake photograph *", type=["jpg", "jpeg", "png"])
        ignore_top = st.slider("Ignore the top part of the photo (sky), %", 0, 50, 20)
        submitted = st.form_submit_button("Submit report")

    if submitted:
        errors = []
        if not lake_name.strip():
            errors.append("Please enter the lake name.")
        if not description.strip():
            errors.append("Please describe the problem.")
        if photo is None:
            errors.append("Please upload a photograph.")
        if latitude == 0 and longitude == 0:
            errors.append("Please enter real latitude and longitude.")
        if photo is not None:
            try:
                Image.open(photo).verify()
                photo.seek(0)
            except Exception:
                errors.append("The uploaded file is not a valid image.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            report_id = generate_report_id()
            image_path = save_image(photo, report_id)
            result = analyse_image(BASE_DIR / image_path, ignore_top_pct=ignore_top)
            report = {
                "Report ID": report_id,
                "Lake Name": lake_name.strip(),
                "Latitude": round(latitude, 6),
                "Longitude": round(longitude, 6),
                "Date/Time": datetime.combine(obs_date, obs_time).strftime("%Y-%m-%d %H:%M:%S"),
                "Description": description.strip(),
                "Image Path": image_path,
                "Pollution Type": result["pollution_type"],
                "Severity": result["severity"],
                "AI Assessment": result["summary"],
                "Complaint Status": "Pollution detected",
            }
            save_report(report)
            st.success(f"Report submitted! Your Report ID is **{report_id}**")
            show_report(report)
            st.image(result["overlay"],
                     caption="Red = areas flagged by the automated assessment",
                     width="stretch")
            st.caption(DISCLAIMER)

with tab_all:
    df = load_reports()
    st.write(f"Total reports: **{len(df)}**")
    if df.empty:
        st.write("No reports yet.")
    else:
        st.dataframe(df, width="stretch")