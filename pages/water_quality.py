"""Water-quality analytics from a PUBLIC dataset (separate from photo assessment)."""
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from src.ui import page_header
from src.reports import BASE_DIR
from src.preprocessing import clean_water_quality
from src.water_quality import train_model, load_saved_model, trend_analysis

page_header("💧 Water Quality Analytics", "Laboratory-based measurements from public datasets.")
st.info("This page uses scientific measurements from a public dataset. It is separate from "
        "the photo-based visual assessment, which cannot measure water quality.")

uploaded = st.file_uploader("Optional: upload a water-quality CSV", type=["csv"])
try:
    df = clean_water_quality(pd.read_csv(uploaded if uploaded else BASE_DIR / "data" / "water_quality.csv"))
except Exception:
    df = None

if df is None or df.shape[1] < 2:
    st.warning("No water-quality dataset found yet.")
    st.markdown("Download a public water-quality CSV (data.gov.in, CPCB / Telangana PCB reports, "
                "or Kaggle), save it as `data/water_quality.csv`, or upload it above.")
    st.stop()

num = df.select_dtypes(include="number").columns.tolist()
st.success(f"Loaded {len(df)} rows and {df.shape[1]} columns ({len(num)} numeric).")
if not num:
    st.stop()

t1, t2, t3, t4 = st.tabs(["Overview", "Distributions & correlation", "Trend (statsmodels)", "ML model (XGBoost)"])

with t1:
    st.dataframe(df.head(50), width="stretch")
    st.dataframe(df.describe(), width="stretch")
    st.write("Missing values per column")
    st.dataframe(df.isna().sum().rename("Missing"), width="stretch")

with t2:
    p = st.selectbox("Parameter", num)
    fig, ax = plt.subplots(figsize=(6, 3.5))
    sns.histplot(df[p].dropna(), kde=True, color="#2563eb", ax=ax)
    st.pyplot(fig)
    if len(num) >= 2:
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.heatmap(df[num].corr(), annot=True, fmt=".2f", cmap="Blues", ax=ax)
        st.pyplot(fig)

with t3:
    date_cols = [c for c in df.columns if "date" in c.lower() or "year" in c.lower()]
    if not date_cols:
        st.write("No date or year column found, so a trend can't be calculated.")
    else:
        dc = st.selectbox("Date column", date_cols)
        tp = st.selectbox("Parameter", num, key="trend_p")
        res = trend_analysis(df, dc, tp)
        if res is None:
            st.write("Not enough dated rows (need at least 5).")
        else:
            fig, ax = plt.subplots(figsize=(7, 3.5))
            ax.plot(res["data"][dc], res["data"][tp], "o-", color="#2563eb", label="Measured")
            ax.plot(res["data"][dc], res["fitted"], "--", color="red", label="Trend line")
            ax.legend()
            st.pyplot(fig)
            direction = "rising" if res["slope_per_year"] > 0 else "falling"
            st.write(f"Trend: **{direction}** by about {res['slope_per_year']:.3f} per year "
                     f"(p-value {res['p_value']:.3f}; below 0.05 suggests the trend is unlikely to be chance).")

with t4:
    target = st.selectbox("Parameter to predict from the others", num, key="ml_t")
    if st.button("Train model"):
        try:
            r = train_model(df, target)
            st.success(f"Model trained and saved to models/water_quality_model.pkl "
                       f"({r['n_train']} train / {r['n_test']} test rows).")
            c1, c2, c3 = st.columns(3)
            c1.metric("R² (test)", r["r2"])
            c2.metric("Error (MAE)", r["mae"])
            c3.metric("Error if guessing the average", r["baseline_mae"])
            st.caption("Compare the model's error with the guess-the-average error. If it isn't "
                       "clearly lower, the model isn't useful. Small datasets give unreliable scores.")
            st.dataframe(r["importance"], width="stretch")
        except ValueError as e:
            st.error(str(e))

    saved = load_saved_model()
    if saved:
        st.subheader(f"Try the saved model (predicts {saved['target']})")
        vals = {f: st.number_input(f, value=float(saved["medians"][f]), key=f"in_{f}")
                for f in saved["features"]}
        if st.button("Predict"):
            pred = saved["model"].predict(pd.DataFrame([vals]))[0]
            st.write(f"Predicted {saved['target']}: **{pred:.2f}**")