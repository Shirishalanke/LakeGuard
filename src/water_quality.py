"""Water-quality analytics: ML model (XGBoost + joblib) and trend analysis (statsmodels)."""
import joblib
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from xgboost import XGBRegressor

from src.reports import BASE_DIR

MODEL_PATH = BASE_DIR / "models" / "water_quality_model.pkl"


def train_model(df: pd.DataFrame, target: str) -> dict:
    """Predict one numeric parameter (e.g. BOD or DO) from the other numeric columns."""
    data = df.dropna(subset=[target])
    features = [c for c in data.select_dtypes(include="number").columns
                if c != target and data[c].notna().any()]
    if len(data) < 30 or not features:
        raise ValueError("Need at least 30 rows with a value for the target and 1+ other numeric column.")

    X_train, X_test, y_train, y_test = train_test_split(
        data[features], data[target], test_size=0.2, random_state=42)
    model = make_pipeline(SimpleImputer(strategy="median"),
                          XGBRegressor(n_estimators=200, max_depth=3,
                                       learning_rate=0.1, random_state=42))
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"model": model, "features": features, "target": target,
                 "medians": data[features].median().to_dict()}, MODEL_PATH)

    importance = pd.DataFrame({"Feature": features,
                               "Importance": model[-1].feature_importances_}
                              ).sort_values("Importance", ascending=False)
    return {"r2": round(r2_score(y_test, pred), 3),
            "mae": round(mean_absolute_error(y_test, pred), 3),
            "baseline_mae": round(mean_absolute_error(y_test, np.full(len(y_test), y_train.mean())), 3),
            "n_train": len(X_train), "n_test": len(X_test), "importance": importance}


def load_saved_model():
    return joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None


def trend_analysis(df: pd.DataFrame, date_col: str, param: str) -> dict | None:
    """Straight-line (OLS) trend of a parameter over time using statsmodels."""
    d = df[[date_col, param]].copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna().sort_values(date_col)
    if len(d) < 5:
        return None
    days = (d[date_col] - d[date_col].min()).dt.days.to_numpy()
    fit = sm.OLS(d[param].to_numpy(), sm.add_constant(days)).fit()
    return {"data": d, "fitted": fit.fittedvalues,
            "slope_per_year": float(fit.params[1] * 365), "p_value": float(fit.pvalues[1])}