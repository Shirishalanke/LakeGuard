"""Home page: search any place and see lakes, ponds, reservoirs and rivers around it."""
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.ui import page_header
from src.reports import load_reports
from src.lake_finder import geocode, find_water, haversine_km

HYDERABAD = (17.385, 78.4867)
COLOURS = {"Lake": "#2563eb", "Pond": "#06b6d4", "Reservoir": "#7c3aed", "River": "#0d9488"}

page_header("🌊 Find Water Bodies Near Any Place",
            "Search a place to see the lakes, ponds, reservoirs and rivers around it.")


@st.cache_data(ttl=3600, show_spinner=False)
def search_water(place: str, radius: int):
    """Cached: the same search twice is instant. Errors are raised so they are not cached."""
    centre = geocode(place)
    if centre is None:
        raise RuntimeError("Place not found. Try adding the city name, e.g. 'Gachibowli, Hyderabad'.")
    items, error = find_water(centre[0], centre[1], radius)
    if error:
        raise RuntimeError(error)
    return centre, items


@st.cache_data(ttl=3600, show_spinner=False)
def geocode_cached(q: str):
    return geocode(q)


# ---------- Search form ----------
with st.form("water_form"):
    c1, c2 = st.columns(2)
    place = c1.text_input("Search a place *", value="Hyderabad",
                          placeholder="e.g. Hyderabad, Gachibowli, Osmania University")
    me = c2.text_input("Your location (optional, to see how far each one is from you)",
                       placeholder="Your area or address")
    radius = st.slider("Search radius (km)", 1, 20, 8)
    go = st.form_submit_button("Search")

if go:
    if not place.strip():
        st.error("Please type a place.")
    else:
        try:
            with st.spinner("Searching... please stay on this page until it finishes."):
                centre, items = search_water(place.strip(), radius)
                you = geocode_cached(me.strip()) if me.strip() else None
            st.session_state.home_res = {"centre": centre, "items": items, "you": you, "radius": radius}
            if me.strip() and you is None:
                st.warning("Your location was not found, so distances are from the searched place.")
        except RuntimeError as e:
            st.error(str(e))

res = st.session_state.get("home_res")

# ---------- Before any search: a quick empty map ----------
if not res:
    m = folium.Map(location=list(HYDERABAD), zoom_start=11, tiles="OpenStreetMap")
    st_folium(m, width=1100, height=460, returned_objects=[])
    st.info("Type a place and click **Search** to see its lakes, ponds, reservoirs and rivers.")
    st.stop()

centre, you, radius = res["centre"], res["you"], res["radius"]
ref = you if you else centre
ref_label = "you" if you else "the searched place"

df = pd.DataFrame(res["items"], columns=["name", "kind", "lat", "lon", "named"])
if len(df):
    df["dist"] = haversine_km(ref[0], ref[1], df["lat"].to_numpy(), df["lon"].to_numpy()).round(2)


def count(kind):
    return int(((df["kind"] == kind) & df["named"]).sum()) if len(df) else 0


# ---------- Counts ----------
st.caption(f"Searched place: {centre[2]}  |  radius {radius} km")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Lakes", count("Lake"))
m2.metric("Ponds", count("Pond"))
m3.metric("Reservoirs", count("Reservoir"))
m4.metric("Rivers", count("River"))
m5.metric("Unnamed water bodies", int((~df["named"]).sum()) if len(df) else 0)
st.caption("Counts are of named water bodies. Unnamed ones are shown separately.")

show_unnamed = st.checkbox("Show unnamed water bodies on the map", value=False)
shown = df if show_unnamed else df[df["named"]] if len(df) else df

# ---------- Map ----------
zoom = 14 if radius <= 3 else 13 if radius <= 6 else 12 if radius <= 12 else 11
m = folium.Map(location=[centre[0], centre[1]], zoom_start=zoom, tiles="OpenStreetMap")
folium.Circle([centre[0], centre[1]], radius=radius * 1000, color="#2563eb",
              fill=False, weight=2).add_to(m)
folium.Marker([centre[0], centre[1]], tooltip="Searched place",
              icon=folium.Icon(color="blue", icon="search")).add_to(m)
if you:
    folium.Marker([you[0], you[1]], tooltip="Your location",
                  icon=folium.Icon(color="green", icon="user")).add_to(m)

for _, w in shown.iterrows():
    folium.CircleMarker(
        [w["lat"], w["lon"]], radius=9 if w["named"] else 4,
        color=COLOURS[w["kind"]], fill=True, fill_opacity=0.75,
        popup=folium.Popup(f"<b>{w['name']}</b><br>Type: {w['kind']}<br>"
                           f"Distance from {ref_label}: {w['dist']} km", max_width=260),
        tooltip=f"{w['name']} ({w['kind']}, {w['dist']} km)").add_to(m)

# LakeGuard citizen reports inside the area
reports = load_reports()
reports["Latitude"] = pd.to_numeric(reports["Latitude"], errors="coerce")
reports["Longitude"] = pd.to_numeric(reports["Longitude"], errors="coerce")
reports = reports.dropna(subset=["Latitude", "Longitude"])
if not reports.empty:
    inside = reports[haversine_km(centre[0], centre[1], reports["Latitude"].to_numpy(),
                                  reports["Longitude"].to_numpy()) <= radius]
    sev = {"High": "red", "Medium": "orange", "Low": "green"}
    for _, r in inside.iterrows():
        folium.CircleMarker([r["Latitude"], r["Longitude"]], radius=4,
                            color=sev.get(r["Severity"], "purple"), fill=True,
                            tooltip=f"LakeGuard report: {r['Lake Name']} ({r['Severity']})").add_to(m)

st_folium(m, width=1100, height=520, returned_objects=[])
st.markdown("🔵 Lake &nbsp; 🩵 Pond &nbsp; 🟣 Reservoir &nbsp; 🟢 River &nbsp;|&nbsp; "
            "small red/orange/green dots = LakeGuard citizen reports")

# ---------- Table ----------
if len(shown):
    table = shown.sort_values("dist")[["name", "kind", "dist"]].rename(
        columns={"name": "Name", "kind": "Type", "dist": f"Distance from {ref_label} (km)"})
    st.dataframe(table, width="stretch", hide_index=True)
    st.download_button("⬇️ Download list (CSV)", table.to_csv(index=False), file_name="water_bodies.csv")
else:
    st.write("Nothing found in this radius. Try a bigger radius or tick the unnamed option.")

st.caption("Data (c) OpenStreetMap contributors. It is volunteer-made, so it may be incomplete or "
           "mislabelled. Distances are straight-line, not road distance. Rivers count only those "
           "tagged as rivers (small nalas and drains are not included). This shows where water "
           "bodies are; it says nothing about their water quality.")