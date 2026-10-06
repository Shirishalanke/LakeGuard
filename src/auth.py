"""User accounts, stored in data/users.csv. Login is by EMAIL (verified with an OTP).
The Phone column is kept (left empty) so older users.csv files still work."""
import re
from datetime import datetime

import pandas as pd

from src.reports import BASE_DIR

USERS_CSV = BASE_DIR / "data" / "users.csv"
USER_COLUMNS = ["Name", "Phone", "Email", "Registered"]


def valid_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", (email or "").strip()))


def load_users() -> pd.DataFrame:
    if USERS_CSV.exists() and USERS_CSV.stat().st_size > 0:
        return pd.read_csv(USERS_CSV, dtype=str).fillna("")
    return pd.DataFrame(columns=USER_COLUMNS)


def find_by_email(email: str):
    """Return the user as a dict, or None."""
    users = load_users()
    match = users[users["Email"].str.lower() == email.strip().lower()]
    return match.iloc[0].to_dict() if len(match) else None


def validate_registration(name: str, email: str):
    """Returns (ok, message)."""
    if not name.strip():
        return False, "Please enter your name."
    if not valid_email(email):
        return False, "Enter a valid email address."
    if find_by_email(email):
        return False, "This email is already registered. Please log in."
    return True, ""


def register_user(name: str, email: str):
    """Save a new user (call this only AFTER the OTP is verified)."""
    ok, msg = validate_registration(name, email)
    if not ok:
        return False, msg
    row = pd.DataFrame([{"Name": name.strip(), "Phone": "", "Email": email.strip().lower(),
                         "Registered": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
    USERS_CSV.parent.mkdir(parents=True, exist_ok=True)
    row.to_csv(USERS_CSV, mode="a", header=not USERS_CSV.exists(), index=False)
    return True, "Registered."