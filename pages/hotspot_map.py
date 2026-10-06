"""Interactive map of pollution hotspots (Folium + streamlit-folium)."""
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.ui import setup_page, page_header
from src.reports import load_reports
from src.hotspot import find_hotspots, single_reports

setup_page("Hotspot Map", "🗺️")
page_header("🗺️ Pollution Hotspot Map",
            "Locations with repeated citizen reports are shown as hotspots.")

df = load_reports()
if df.empty:
    st.info("No reports yet. Submit reports on the Citizen Report page first.")
    st.stop()

radius = st.slider("Merge reports within (metres)", 50, 500, 150, step=50,
                   help="Reports closer than this are treated as ONE hotspot.")

hotspots = find_hotspots(df, radius_m=radius)
singles = single_reports(df, hotspots)

st.markdown("🔴 **High** hotspot  &nbsp;&nbsp; 🟠 **Moderate** hotspot  &nbsp;&nbsp; "
            "🟢 **Low** hotspot  &nbsp;&nbsp; ⚪ single report (not a hotspot yet)")

# ---------- Build the map ----------
df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
centre = [df["Latitude"].mean(), df["Longitude"].mean()]
m = folium.Map(location=centre, zoom_start=13, tiles="OpenStreetMap")

COLOURS = {"High": "red", "Moderate": "orange", "Low": "green"}

for _, h in hotspots.iterrows():
    popup = (f"<b>{h['Lake']}</b><br>Level: {h['Level']}<br>"
             f"Reports: {h['Reports']}<br>IDs: {h['Report IDs']}")
    folium.CircleMarker(
        location=[h["Latitude"], h["Longitude"]],
        radius=10 + 3 * int(h["Reports"]),          # bigger circle = more reports
        color=COLOURS[h["Level"]], fill=True, fill_opacity=0.55,
        popup=folium.Popup(popup, max_width=300),
        tooltip=f"{h['Level']} hotspot: {h['Lake']}",
    ).add_to(m)

for _, r in singles.dropna(subset=["Latitude", "Longitude"]).iterrows():
    folium.CircleMarker(
        location=[r["Latitude"], r["Longitude"]], radius=5,
        color="gray", fill=True, fill_opacity=0.8,
        popup=f"{r['Report ID']}<br>{r['Lake Name']}<br>Severity: {r['Severity']}",
    ).add_to(m)

# returned_objects=[] stops the page from reloading every time you click the map
st_folium(m, width=1100, height=550, returned_objects=[])

# ---------- Hotspot table ----------
c1, c2 = st.columns(2)
c1.metric("Hotspots found", len(hotspots))
c2.metric("Single reports", len(singles))

if len(hotspots):
    st.subheader("Hotspot list")
    st.dataframe(hotspots.sort_values("Score", ascending=False), width="stretch")
else:
    st.caption("No hotspots yet. A hotspot needs 2 or more reports close together.")

st.caption("Hotspots are based on the number and severity of citizen reports. "
           "They show where visible pollution is reported repeatedly, not measured water quality.")