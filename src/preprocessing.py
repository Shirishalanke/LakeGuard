"""Preprocessing for images and for the water-quality CSV."""
import pandas as pd
from PIL import Image


def load_image(path, max_side: int = 600) -> Image.Image:
    """Open a photo as RGB and shrink it so analysis is fast."""
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_side, max_side))
    return img


def clean_water_quality(df: pd.DataFrame) -> pd.DataFrame:
    """Tidy a public water-quality table: strip column names, drop duplicate rows,
    and turn number-like text columns ('7.2', 'NA', 'BDL') into numbers."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.drop_duplicates()
    for col in df.columns:
        if df[col].dtype == object:
            as_num = pd.to_numeric(df[col], errors="coerce")
            if as_num.notna().mean() >= 0.7:      # mostly numbers -> treat as numeric
                df[col] = as_num
    return df