"""Lake Finder page: search any place, see nearby lakes, the count and distances."""
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.ui import page_header
from src.reports import load_reports
from src.lake_finder import geocode, find_lakes, haversine_km

page_header("🔎 Lake Finder",
            "Search any place to see the lakes around it, how many there are and how far they are.")

with st.form("lake_form"):
    c1, c2 = st.columns(2)
    place = c1.text_input("Search a place *", value="Hyderabad",
                          placeholder="e.g. Osmania University, Hyderabad")
    me = c2.text_input("Your location (optional)",
                       placeholder="Your area or address. Leave blank to measure from the searched place")
    radius = st.slider("Search radius (km)", 1, 30, 10)
    go = st.form_submit_button("Find lakes")

# ---------- Search (runs only when the button is pressed) ----------
if go:
    if not place.strip():
        st.error("Please type a place to search.")
    else:
        with st.spinner("Searching..."):
            centre = geocode(place.strip())
            if centre is None:
                st.error("Place not found (or the search service is unreachable). Try adding the city name.")
            else:
                lakes, error = find_lakes(centre[0], centre[1], radius)
                if error:
                    st.error(error)
                else:
                    you = geocode(me.strip()) if me.strip() else None
                    if me.strip() and you is None:
                        st.warning("Your location was not found, so distances are measured from the searched place.")
                    st.session_state.lf = {"centre": centre, "you": you, "lakes": lakes,
                                           "radius": radius, "place": place.strip()}

# ---------- Show results (kept in session so the map doesn't vanish on reruns) ----------
res = st.session_state.get("lf")
if not res:
    st.info("Enter a place and click **Find lakes**.")
    st.stop()

centre, you, radius = res["centre"], res["you"], res["radius"]
ref = you if you else centre                       # distances are measured from here
ref_label = "you" if you else "the searched place"

rows = []
for lake in res["lakes"]:
    rows.append({**lake, "dist": float(haversine_km(ref[0], ref[1], lake["lat"], lake["lon"]))})
df = pd.DataFrame(rows)

show_unnamed = st.checkbox("Include unnamed water bodies", value=False)
if len(df) and not show_unnamed:
    shown = df[df["named"]]
else:
    shown = df
shown = shown.sort_values("dist") if len(shown) else shown

# LakeGuard reports near each lake (within 500 m)
reports = load_reports()
reports["Latitude"] = pd.to_numeric(reports["Latitude"], errors="coerce")
reports["Longitude"] = pd.to_numeric(reports["Longitude"], errors="coerce")
reports = reports.dropna(subset=["Latitude", "Longitude"])


def reports_near(lat, lon, km=0.5):
    if reports.empty:
        return 0
    return int((haversine_km(lat, lon, reports["Latitude"].to_numpy(),
                             reports["Longitude"].to_numpy()) <= km).sum())


# ---------- Numbers ----------
st.caption(f"Searched place: {centre[2]}")
n_named = int(df["named"].sum()) if len(df) else 0
n_unnamed = len(df) - n_named
m1, m2, m3, m4 = st.columns(4)
m1.metric("Named lakes found", n_named)
m2.metric("Unnamed water bodies", n_unnamed)
if len(shown):
    nearest = shown.iloc[0]
    m3.metric(f"Nearest to {ref_label}", f"{nearest['dist']:.1f} km")
    m4.metric("Nearest lake", nearest["name"][:22])
else:
    m3.metric(f"Nearest to {ref_label}", "-")
    m4.metric("Nearest lake", "-")

# ---------- Map ----------
zoom = 14 if radius <= 3 else 13 if radius <= 8 else 12 if radius <= 15 else 11
m = folium.Map(location=[centre[0], centre[1]], zoom_start=zoom, tiles="OpenStreetMap")
folium.Circle([centre[0], centre[1]], radius=radius * 1000, color="#2563eb",
              fill=False, weight=2).add_to(m)
folium.Marker([centre[0], centre[1]], tooltip="Searched place",
              icon=folium.Icon(color="blue", icon="search")).add_to(m)
if you:
    folium.Marker([you[0], you[1]], tooltip="Your location",
                  icon=folium.Icon(color="green", icon="user")).add_to(m)

for _, lk in shown.iterrows():
    popup = (f"<b>{lk['name']}</b><br>Type: {lk['kind']}<br>"
             f"Distance from {ref_label}: {lk['dist']:.2f} km<br>"
             f"LakeGuard reports within 500 m: {reports_near(lk['lat'], lk['lon'])}")
    folium.CircleMarker([lk["lat"], lk["lon"]], radius=9,
                        color="#0369a1" if lk["named"] else "gray",
                        fill=True, fill_opacity=0.7,
                        popup=folium.Popup(popup, max_width=280),
                        tooltip=f"{lk['name']} ({lk['dist']:.1f} km)").add_to(m)

# LakeGuard citizen reports inside the search area
COLORS = {"High": "red", "Medium": "orange", "Low": "green"}
if not reports.empty:
    inside = reports[haversine_km(centre[0], centre[1], reports["Latitude"].to_numpy(),
                                  reports["Longitude"].to_numpy()) <= radius]
    for _, r in inside.iterrows():
        folium.CircleMarker([r["Latitude"], r["Longitude"]], radius=4,
                            color=COLORS.get(r["Severity"], "purple"), fill=True,
                            tooltip=f"LakeGuard report: {r['Lake Name']} ({r['Severity']})").add_to(m)

st_folium(m, width=1100, height=550, returned_objects=[])
st.caption("🔵 lake / reservoir  ⚪ unnamed water body  🔴🟠🟢 LakeGuard citizen reports  "
           "🟦 searched place  🟩 you")

# ---------- Table ----------
if len(shown):
    table = pd.DataFrame({
        "Lake": shown["name"],
        "Type": shown["kind"],
        f"Distance from {ref_label} (km)": shown["dist"].round(2),
        "LakeGuard reports within 500 m": [reports_near(a, b) for a, b in zip(shown["lat"], shown["lon"])],
    })
    st.dataframe(table, width="stretch", hide_index=True)
    st.download_button("⬇️ Download list (CSV)", table.to_csv(index=False),
                       file_name="nearby_lakes.csv")
else:
    st.write("No lakes found in this radius. Try a bigger radius or tick the unnamed option.")

st.caption("Lake data (c) OpenStreetMap contributors. It may be incomplete or mislabelled, and "
           "distances are straight-line, not road distance. This shows where lakes are; it says "
           "nothing about their water quality.")