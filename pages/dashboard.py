"""Dashboard: summary numbers and charts built from citizen reports."""
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from src.ui import page_header
from src.reports import load_reports
from src.hotspot import find_hotspots

page_header("📊 Dashboard", "Pollution reports at a glance.")

df = load_reports()

# Safety net: these columns must always exist, even if the CSV is old or incomplete
for col in ("Severity", "Pollution Type", "Complaint Status", "Date/Time"):
    if col not in df.columns:
        df[col] = "Pending"
for col in ("Severity", "Pollution Type", "Complaint Status"):
    df[col] = df[col].fillna("Pending").replace("", "Pending")

if df.empty:
    st.info("No reports yet. Charts will appear after the first report is submitted.")
    st.stop()

# ---------- Summary numbers ----------
done = ["Cleanup completed", "AI verification"]
total = len(df)
high = int((df["Severity"] == "High").sum())
completed = int(df["Complaint Status"].isin(done).sum())
active = total - completed

try:
    n_hotspots = len(find_hotspots(df))
except Exception:
    n_hotspots = 0          # never let the hotspot step break the dashboard

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total reports", total)
c2.metric("High severity", high)
c3.metric("Active complaints", active)
c4.metric("Completed cleanups", completed)
c5.metric("Hotspots", n_hotspots)

st.write("")
sns.set_theme(style="whitegrid")


def bar_chart(series, title, color):
    """Small bar chart from a pandas Series of counts."""
    fig, ax = plt.subplots(figsize=(5, 3.2))
    sns.barplot(x=series.index.astype(str), y=series.values, color=color, ax=ax)
    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel("Reports")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout()
    return fig


left, right = st.columns(2)
with left:
    st.pyplot(bar_chart(df["Severity"].value_counts(), "Severity distribution", "#2563eb"))
with right:
    types = df["Pollution Type"].astype(str).str.slice(0, 28).value_counts()
    st.pyplot(bar_chart(types, "Pollution types", "#0ea5e9"))

left2, right2 = st.columns(2)
with left2:
    st.pyplot(bar_chart(df["Complaint Status"].value_counts(), "Complaint status", "#1e3a8a"))
with right2:
    dates = pd.to_datetime(df["Date/Time"], errors="coerce").dt.date.dropna()
    if len(dates):
        per_day = dates.value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(5, 3.2))
        sns.lineplot(x=list(per_day.index), y=per_day.values, marker="o",
                     color="#2563eb", ax=ax)
        ax.set_title("Reports over time")
        ax.set_xlabel("")
        ax.set_ylabel("Reports")
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        fig.tight_layout()
        st.pyplot(fig)
    else:
        st.info("No valid dates to chart yet.")

st.caption("Severity and pollution type come from the automated visual assessment of "
           "each photo; they are not water-quality measurements. The interactive map and "
           "water-quality analytics have their own pages.")