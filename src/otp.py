"""Email one-time passwords (OTP): create, send and verify.
The OTP is stored only as a hash and expires after 5 minutes (any number of tries).
If no SMTP settings are in .env, DEMO MODE shows the code on screen (not secure)."""
import hashlib
import os
import secrets
import smtplib
import time
from email.message import EmailMessage

from dotenv import load_dotenv

from src.reports import BASE_DIR

load_dotenv(BASE_DIR / ".env")

OTP_VALID_SECONDS = 300


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def email_ready() -> bool:
    return all(os.getenv(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"))


def _send_email(to: str, code: str) -> None:
    """Send the code. Tries the configured port first, then Gmail's SSL port 465."""
    msg = EmailMessage()
    msg["Subject"] = "LakeGuard AI login code"
    msg["From"] = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER")
    msg["To"] = to
    msg.set_content(f"Your LakeGuard AI one-time code is {code}.\n"
                    f"It is valid for {OTP_VALID_SECONDS // 60} minutes. Do not share it.")

    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD").replace(" ", "")   # Gmail shows app passwords with spaces
    port = int(os.getenv("SMTP_PORT", "587"))
    attempts = [("ssl", 465)] if port == 465 else [("starttls", port), ("ssl", 465)]

    last_error = None
    for mode, p in attempts:
        try:
            if mode == "ssl":
                with smtplib.SMTP_SSL(host, p, timeout=20) as s:
                    s.login(user, password)
                    s.send_message(msg)
            else:
                with smtplib.SMTP(host, p, timeout=20) as s:
                    s.ehlo()
                    s.starttls()
                    s.ehlo()
                    s.login(user, password)
                    s.send_message(msg)
            return
        except smtplib.SMTPAuthenticationError:
            raise                              # wrong password: trying another port won't help
        except Exception as e:
            last_error = e
    raise last_error


def create_otp(email: str):
    """Returns (state, message). state is None if sending failed."""
    code = f"{secrets.randbelow(10**6):06d}"
    demo_code = None
    try:
        if email_ready():
            _send_email(email, code)
            msg = f"A code was sent to {email}. Check your inbox (and spam folder)."
        else:
            demo_code = code
            msg = "Demo mode: no email service is configured in .env."
    except smtplib.SMTPAuthenticationError:
        return None, ("Gmail rejected the login. Check SMTP_USER and use a Gmail "
                      "App password (not your normal password) in .env.")
    except Exception as e:
        return None, (f"Could not send the email ({type(e).__name__}). Check your internet "
                      "connection, then try again in a few seconds.")
    state = {"email": email, "hash": _hash(code), "expires": time.time() + OTP_VALID_SECONDS,
             "demo_code": demo_code, "message": msg}
    return state, msg


def verify_otp(state: dict, entered: str):
    """Returns (ok, message). No limit on attempts, but the code expires."""
    if time.time() > state["expires"]:
        return False, "This code has expired. Please request a new one."
    if secrets.compare_digest(_hash(entered.strip()), state["hash"]):
        return True, "Verified."
    return False, "Wrong code. Please try again."