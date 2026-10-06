# 🌊 LakeGuard AI: Lake Pollution Reporting & Cleanup Portal

**Live demo:** https://lakeguard-djfbrh49kmcyfvwpyr6rrv.streamlit.app/

LakeGuard AI is a college project that helps citizens report visible pollution in Hyderabad lakes and follow the cleanup. It is an **independent citizen platform and is not operated by GHMC**. It is a decision-support tool, not a replacement for field inspection or laboratory testing.

## Features

| Page | What it does |
|---|---|
| 🔐 Email OTP login | Verifies that the citizen owns the email address |
| 🏠 Home / Water-body finder | Search any place and see lakes, ponds, reservoirs and rivers on a map, with counts and distances (OpenStreetMap data) |
| 📝 Report Pollution | Upload a lake photo with location and description; get an automated visual assessment |
| 🗺️ Hotspot Map | Groups nearby reports into one hotspot (no duplicates) on an interactive Folium map |
| 📊 Dashboard | Totals, severity, pollution types, complaint status and reports over time |
| 💧 Water Quality | Analytics on public water-quality data: statistics, trend analysis (statsmodels) and an XGBoost model saved with joblib |
| 📨 GHMC Complaint | Builds a ready-to-file complaint and links to the official GHMC website |
| 🧹 Cleanup Tracking | Admin updates status, uploads before/after photos and runs a visual cleanup comparison |

## How it works

Citizen reports pollution → automated visual assessment of the photo → repeated reports form hotspots → dashboard shows priorities → complaint is prepared for the official GHMC channel → cleanup is tracked → before/after photos are compared.

## Tech stack

Python · Streamlit · pandas · NumPy · scikit-learn · XGBoost · statsmodels · joblib · Folium · streamlit-folium · matplotlib · seaborn · geopy · OpenStreetMap (Nominatim and Overpass)

## Run it locally

```
py -3.11 -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Create a `.env` file for email OTP (never upload it to GitHub):

```
ADMIN_PASSWORD=choose-a-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youraddress@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM=youraddress@gmail.com
```

With the SMTP lines empty, the app runs in demo mode and shows the OTP on screen (not secure).

## Project structure

```
app.py          login and top navigation
pages/          one file per page
src/            logic: auth, otp, reports, pollution_detection, severity,
                hotspot, water_quality, preprocessing, complaint, lake_finder, ui
data/           CSV files
images/         report, before and after photos
models/         saved model (created when you click Train)
notebooks/      analysis notebook
```

## Honest limitations

- The photo detector is a **rule-based colour-and-edge method; nothing in it is trained**, and no accuracy figure is claimed. It can flag non-waste objects and miss real waste.
- A photograph **cannot measure water quality** (pH, DO, BOD, COD). That is why the Water Quality page uses a separate public dataset.
- Visual cleanup verification compares two photos only. It is not proof of restored water quality.
- There is **no GHMC API integration**. The app prepares a complaint, and the citizen files it on the official GHMC channel.
- GPS can be inaccurate, and reports can be duplicated or false.
- Water-body data from OpenStreetMap is volunteer-made and may be incomplete. Distances are straight-line.
- Data is stored in CSV files. On the hosted demo it is temporary and resets when the app restarts.
- Photos, emails and coordinates are personal data and need proper protection in any real deployment.

## Future work

Trained image classifier on a labelled dataset, database storage, a "My reports" page, and more public water-quality datasets.

## Author

Shirisha Lanke · College project · [GitHub](https://github.com/Shirishalanke)
