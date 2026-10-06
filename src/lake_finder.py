"""Find water bodies (lakes, ponds, reservoirs, rivers) around a place.
- geocode():    place name -> latitude/longitude (OpenStreetMap Nominatim via geopy)
- find_water(): water bodies around a point (OpenStreetMap Overpass API)
Free services, need internet. Data (c) OpenStreetMap contributors."""
import numpy as np
import requests
from geopy.geocoders import Nominatim

OVERPASS_URLS = ["https://overpass-api.de/api/interpreter",
                 "https://overpass.kumi.systems/api/interpreter"]
HEADERS = {"User-Agent": "LakeGuardAI-college-project/1.0"}


def haversine_km(lat1, lon1, lat2, lon2):
    """Straight-line distance in km (single numbers or numpy arrays)."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def geocode(query: str):
    """Returns (lat, lon, address) or None."""
    try:
        loc = Nominatim(user_agent="LakeGuardAI-college-project", timeout=8).geocode(query)
    except Exception:
        return None
    return None if loc is None else (loc.latitude, loc.longitude, loc.address)


def find_water(lat: float, lon: float, radius_km: float):
    """Returns (items, error). Each item: name, kind (Lake/Pond/Reservoir/River), lat, lon, named."""
    a = f"(around:{int(radius_km * 1000)},{lat},{lon})"
    query = f"""[out:json][timeout:25];
(
  nwr["natural"="water"]["water"~"^(lake|pond|reservoir)$"]{a};
  nwr["landuse"="reservoir"]{a};
  nwr["natural"="water"]["name"][!"water"]{a};
  way["waterway"="river"]["name"]{a};
  relation["waterway"="river"]["name"]{a};
);
out center tags;"""

    elements, last_error = None, None
    for url in OVERPASS_URLS:
        try:
            resp = requests.post(url, data={"data": query}, headers=HEADERS, timeout=25)
            resp.raise_for_status()
            elements = resp.json().get("elements", [])
            break
        except Exception as e:
            last_error = e
    if elements is None:
        return None, (f"The map data service is busy or unreachable ({type(last_error).__name__}). "
                      "Try again in a minute, or use a smaller radius.")

    items, rivers = [], {}
    for el in elements:
        tags = el.get("tags", {})
        c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
        if c.get("lat") is None:
            continue
        name = tags.get("name:en") or tags.get("name")

        if tags.get("waterway") == "river":          # a river has many segments: keep the nearest one
            if not name:
                continue
            d = float(haversine_km(lat, lon, c["lat"], c["lon"]))
            if name.lower() not in rivers or d < rivers[name.lower()]["d"]:
                rivers[name.lower()] = {"name": name, "kind": "River", "lat": c["lat"],
                                        "lon": c["lon"], "named": True, "d": d}
            continue

        water = tags.get("water")
        if water == "pond":
            kind = "Pond"
        elif water == "reservoir" or tags.get("landuse") == "reservoir":
            kind = "Reservoir"
        else:
            kind = "Lake"
        item = {"name": name or f"Unnamed {kind.lower()}", "kind": kind,
                "lat": c["lat"], "lon": c["lon"], "named": bool(name)}

        # One lake is often drawn as several polygons, so remove duplicates
        dup = False
        for o in items:
            if o["kind"] != kind:
                continue
            d = float(haversine_km(item["lat"], item["lon"], o["lat"], o["lon"]))
            if item["named"] and o["named"] and item["name"].lower() == o["name"].lower() and d < 1.5:
                dup = True
            elif not item["named"] and not o["named"] and d < 0.05:
                dup = True
            if dup:
                break
        if not dup:
            items.append(item)

    for r in rivers.values():
        r.pop("d")
        items.append(r)
    return items, None