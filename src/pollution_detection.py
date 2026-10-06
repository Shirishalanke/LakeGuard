"""Automated VISUAL assessment of a lake photograph (not a water-quality measurement).

How it works (no trained model):
  1. Ignore the top part of the photo (sky) - the user can change this.
  2. Find BRIGHT, low-colour pixels   -> possible plastic / foam
  3. Find strongly COLOURED pixels that are not blue/green -> possible coloured items
  4. Keep only blobs with sharp edges and a sensible size (clouds are soft and huge)
  5. % of the analysed area covered by kept blobs = 'visible area'
"""
import numpy as np
from PIL import Image
from scipy import ndimage  # installed together with scikit-learn

from src.preprocessing import load_image
from src.severity import severity_from_area, reduction_percent

DISCLAIMER = ("Automated visual assessment of a photograph. It is NOT a scientific or "
              "laboratory measurement of water quality, and it can be wrong.")


def _keep_object_like_blobs(mask, grad, roi_pixels):
    """Keep blobs that are not tiny noise, not huge (sky/buildings) and have sharp edges."""
    mask = ndimage.binary_opening(mask, iterations=1)
    labels, _ = ndimage.label(mask)
    keep = np.zeros_like(mask)
    min_area, max_area = 0.0004 * roi_pixels, 0.25 * roi_pixels
    for i, sl in enumerate(ndimage.find_objects(labels), start=1):
        comp = labels[sl] == i
        area = comp.sum()
        if area < min_area or area > max_area:
            continue
        edge = comp & ~ndimage.binary_erosion(comp)
        if edge.any() and grad[sl][edge].mean() >= 60:      # sharp outline
            keep[sl] |= comp
    return keep


def analyse_image(image_path, ignore_top_pct: int = 20) -> dict:
    img = load_image(image_path)
    rgb = np.asarray(img)
    hsv = np.asarray(img.convert("HSV")).astype(float)
    hue, sat, val = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255

    gray = rgb.mean(axis=2)
    grad = np.hypot(ndimage.sobel(gray, axis=1), ndimage.sobel(gray, axis=0))

    height, width = gray.shape
    cut = int(height * ignore_top_pct / 100)
    roi_pixels = max((height - cut) * width, 1)

    bright = (val > 0.80) & (sat < 0.20)
    colourful = (sat > 0.55) & (val > 0.45) & ~((hue >= 70) & (hue <= 260))
    bright[:cut] = False
    colourful[:cut] = False

    bright = _keep_object_like_blobs(bright, grad, roi_pixels)
    colourful = _keep_object_like_blobs(colourful, grad, roi_pixels)
    flagged = bright | colourful

    bright_pct = round(bright.sum() / roi_pixels * 100, 1)
    colour_pct = round(colourful.sum() / roi_pixels * 100, 1)
    area_pct = round(flagged.sum() / roi_pixels * 100, 1)

    types = []
    if bright_pct >= 1:
        types.append("Plastic / foam-like floating objects")
    if colour_pct >= 1:
        types.append("Coloured floating items")
    if area_pct >= 15:
        types.append("Garbage accumulation (possible)")
    pollution_type = "; ".join(types) if types else "No visible pollution detected"
    severity = severity_from_area(area_pct)

    # Overlay: flagged pixels in red, ignored sky area dimmed
    overlay = rgb.copy()
    overlay[flagged] = (0.4 * overlay[flagged] + 0.6 * np.array([255, 0, 0])).astype(np.uint8)
    overlay[:cut] = (overlay[:cut] * 0.5).astype(np.uint8)

    summary = (f"Automated visual assessment: about {area_pct}% of the analysed area "
               f"flagged ({pollution_type}). Not a water-quality measurement.")
    return {"area_pct": area_pct, "bright_pct": bright_pct, "colour_pct": colour_pct,
            "severity": severity, "pollution_type": pollution_type, "summary": summary,
            "overlay": Image.fromarray(overlay)}


def visual_cleanup_verification(before_path, after_path, ignore_top_pct: int = 20) -> dict:
    """Compare two photos. Works best if both were taken from the same spot and angle."""
    b = analyse_image(before_path, ignore_top_pct)
    a = analyse_image(after_path, ignore_top_pct)
    return {"before_pct": b["area_pct"], "after_pct": a["area_pct"],
            "reduction_pct": reduction_percent(b["area_pct"], a["area_pct"]),
            "before_overlay": b["overlay"], "after_overlay": a["overlay"]}


if __name__ == "__main__":
    # Quick test from the terminal:  python -m src.pollution_detection path/to/photo.jpg
    import sys
    result = analyse_image(sys.argv[1])
    result.pop("overlay").save("data/processed/overlay_test.png")
    print(result)