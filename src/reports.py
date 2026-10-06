"""Helper functions for saving and loading citizen reports (CSV + images)
and for cleanup tracking (status updates + before/after photos)."""
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent      # the LakeGuard-AI folder
REPORTS_CSV = BASE_DIR / "data" / "citizen_reports.csv"
REPORT_IMAGES_DIR = BASE_DIR / "images" / "reports"
BEFORE_DIR = BASE_DIR / "images" / "before"
AFTER_DIR = BASE_DIR / "images" / "after"

COLUMNS = [
    "Report ID", "Lake Name", "Latitude", "Longitude", "Date/Time",
    "Description", "Image Path", "Pollution Type", "Severity",
    "AI Assessment", "Complaint Status",
]

STATUSES = [
    "Pollution detected", "Complaint prepared", "Complaint submitted",
    "Cleanup assigned", "Cleanup completed", "AI verification",
]


# ---------- Citizen reports ----------
def generate_report_id() -> str:
    """Unique ID like LG-20261004-A1B2C3."""
    return f"LG-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"


def save_image(uploaded_file, report_id: str) -> str:
    """Save photo to images/reports/ and return its relative path."""
    REPORT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(uploaded_file.name).suffix.lower() or ".jpg"
    path = REPORT_IMAGES_DIR / f"{report_id}{ext}"
    path.write_bytes(uploaded_file.getbuffer())
    return path.relative_to(BASE_DIR).as_posix()


def save_report(report: dict) -> None:
    """Add one report. The whole file is rewritten with the correct header."""
    REPORTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    row = pd.DataFrame([report], columns=COLUMNS)
    existing = load_reports()
    combined = pd.concat([existing, row], ignore_index=True) if len(existing) else row
    combined.to_csv(REPORTS_CSV, index=False)


def load_reports() -> pd.DataFrame:
    """Read all reports. ALWAYS returns every expected column, even if the CSV
    has an older, misspelt or incomplete header."""
    if not (REPORTS_CSV.exists() and REPORTS_CSV.stat().st_size > 0):
        return pd.DataFrame(columns=COLUMNS)

    try:
        df = pd.read_csv(REPORTS_CSV)
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

    # Tidy header names (extra spaces / different capital letters)
    lookup = {c.lower(): c for c in COLUMNS}
    df.columns = [lookup.get(str(c).strip().lower(), str(c).strip()) for c in df.columns]

    # Add any missing column with a sensible default
    defaults = {"Pollution Type": "Pending", "Severity": "Pending",
                "AI Assessment": "Pending", "Complaint Status": "Pollution detected"}
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = defaults.get(col, "")
    return df[COLUMNS]


def show_report(report: dict) -> None:
    """Display one report on screen."""
    st.subheader(f"Report {report['Report ID']}")
    c1, c2 = st.columns(2)
    with c1:
        st.image(str(BASE_DIR / report["Image Path"]), caption="Submitted photograph",
                 width="stretch")
    with c2:
        st.write(f"**Lake:** {report['Lake Name']}")
        st.write(f"**Location:** {report['Latitude']}, {report['Longitude']}")
        st.write(f"**Date/Time:** {report['Date/Time']}")
        st.write(f"**Description:** {report['Description']}")
        st.write(f"**Pollution type:** {report['Pollution Type']}")
        st.write(f"**Severity:** {report['Severity']}")
        st.write(f"**AI assessment:** {report['AI Assessment']}")
        st.write(f"**Complaint status:** {report['Complaint Status']}")


# ---------- Cleanup tracking ----------
def update_status(report_id: str, new_status: str) -> None:
    """Change the complaint status of one report in the CSV."""
    df = load_reports()
    df.loc[df["Report ID"] == report_id, "Complaint Status"] = new_status
    df.to_csv(REPORTS_CSV, index=False)


def save_cleanup_photo(uploaded_file, report_id: str, kind: str) -> None:
    """kind is 'before' or 'after'. Saves as images/<kind>/<report_id>.<ext>."""
    folder = BEFORE_DIR if kind == "before" else AFTER_DIR
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob(f"{report_id}.*"):      # replace any older photo
        old.unlink()
    ext = Path(uploaded_file.name).suffix.lower() or ".jpg"
    (folder / f"{report_id}{ext}").write_bytes(uploaded_file.getbuffer())


def find_cleanup_photo(report_id: str, kind: str):
    """Return the saved photo path, or None if there isn't one."""
    folder = BEFORE_DIR if kind == "before" else AFTER_DIR
    matches = list(folder.glob(f"{report_id}.*"))
    return matches[0] if matches else None