# LakeGuard AI - Lake Pollution Reporting & Cleanup Portal (Hyderabad)

A college project. LakeGuard AI is an **independent citizen platform and is not operated by GHMC**.
It is a decision-support tool: it does not replace field inspection or laboratory testing.

## What it does
| Page | Purpose |
|---|---|
| Login (email + OTP) | Verifies the citizen owns the email address |
| Report Pollution | Photo + lake name + location + description; automated visual assessment |
| Hotspot Map | Groups nearby reports into hotspots (Folium map) |
| Dashboard | Totals, severity, pollution types, status and reports over time |
| Water Quality | Public-dataset analytics, statsmodels trend, XGBoost model saved with joblib |
| GHMC Complaint | Builds a ready-to-file complaint and links to the official GHMC website |
| Cleanup Tracking | Admin updates status, uploads before/after photos, visual cleanup verification |

## Setup (Windows, VS Code terminal)
```
py -3.11 -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Open http://localhost:8501

## Configuration (`.env`)
```
ADMIN_PASSWORD=choose-a-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youraddress@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM=youraddress@gmail.com
```
With the SMTP lines empty the app runs in **demo mode**: the OTP is shown on screen (not secure).
Never upload `.env` to GitHub.

## Project structure
```
app.py              login + top navigation
pages/              one file per page
src/                logic: auth, otp, reports, pollution_detection, severity, hotspot,
                    water_quality, preprocessing, complaint, ui
data/               CSV files (reports, users, water quality)
images/             report, before and after photos
models/             water_quality_model.pkl (created when you click Train)
notebooks/          lakeguard_analysis.ipynb
```

## Honest limitations
- The photo detector is a **rule-based colour-and-edge method; nothing in it is trained** and no accuracy figure is claimed. It can flag non-waste objects and miss real waste.
- A photograph cannot measure water quality (pH, DO, BOD, COD). Those need sensors or laboratory data, which is why the Water Quality page uses a separate public dataset.
- Visual cleanup verification compares two photos only. It is not proof of restored water quality.
- GPS can be inaccurate, and citizen reports can be duplicated or false.
- There is no GHMC API integration. The app prepares a complaint; the citizen files it on the official GHMC channel.
- Data is stored in CSV files, which is fine for a demo but not for many simultaneous users.
- Photos, emails and coordinates are personal data and need protection in any real deployment.

## Future work
Trained image classifier on a labelled dataset, SQLite/database storage, "My reports" page, more public datasets.