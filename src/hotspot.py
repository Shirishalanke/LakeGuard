"""Hotspot detection: groups nearby reports so one location = one hotspot."""
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

EARTH_RADIUS_M = 6_371_000
WEIGHTS = {"High": 3, "Medium": 2, "Low": 1, "Pending": 1}


def level_from_score(score: int) -> str:
    """Turn a total score into a hotspot level."""
    if score >= 6:
        return "High"
    if score >= 3:
        return "Moderate"
    return "Low"


def find_hotspots(df: pd.DataFrame, radius_m: int = 150, min_reports: int = 2) -> pd.DataFrame:
    """Return one row per hotspot (a group of nearby reports).

    radius_m    : reports closer than this (metres) are merged into one hotspot
    min_reports : minimum reports in a group to call it a hotspot
    """
    cols = ["Lake", "Latitude", "Longitude", "Reports", "Score", "Level", "Report IDs"]
    if df.empty:
        return pd.DataFrame(columns=cols)

    data = df.copy()
    data["Latitude"] = pd.to_numeric(data["Latitude"], errors="coerce")
    data["Longitude"] = pd.to_numeric(data["Longitude"], errors="coerce")
    data = data.dropna(subset=["Latitude", "Longitude"]).reset_index(drop=True)
    if len(data) < min_reports:
        return pd.DataFrame(columns=cols)

    # DBSCAN with the haversine metric groups points by real-world distance
    coords = np.radians(data[["Latitude", "Longitude"]].to_numpy())
    labels = DBSCAN(eps=radius_m / EARTH_RADIUS_M, min_samples=min_reports,
                    metric="haversine", algorithm="ball_tree").fit_predict(coords)
    data["cluster"] = labels

    rows = []
    for label, group in data[data["cluster"] != -1].groupby("cluster"):   # -1 = not in a group
        score = int(group["Severity"].map(WEIGHTS).fillna(1).sum())
        rows.append({
            "Lake": group["Lake Name"].mode().iloc[0],
            "Latitude": group["Latitude"].mean(),
            "Longitude": group["Longitude"].mean(),
            "Reports": len(group),
            "Score": score,
            "Level": level_from_score(score),
            "Report IDs": ", ".join(group["Report ID"]),
        })
    return pd.DataFrame(rows, columns=cols)


def single_reports(df: pd.DataFrame, hotspots: pd.DataFrame) -> pd.DataFrame:
    """Reports that are NOT part of any hotspot."""
    used = set(", ".join(hotspots["Report IDs"]).split(", ")) if len(hotspots) else set()
    return df[~df["Report ID"].isin(used)]