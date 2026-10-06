"""Severity rules. These thresholds are our own choice, NOT a scientific standard.
Change LOW_MAX / MEDIUM_MAX if you want different cut-offs."""
LOW_MAX = 5       # up to 5% of the analysed area flagged  -> Low
MEDIUM_MAX = 15   # 5% to 15% -> Medium, above 15% -> High


def severity_from_area(area_pct: float) -> str:
    if area_pct <= LOW_MAX:
        return "Low"
    if area_pct <= MEDIUM_MAX:
        return "Medium"
    return "High"


def reduction_percent(before_pct: float, after_pct: float) -> float:
    """Estimated visual reduction, e.g. 40% -> 10% gives 75%."""
    if before_pct <= 0:
        return 0.0
    return round(max(0.0, (before_pct - after_pct) / before_pct * 100), 1)