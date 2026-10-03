import json
import logging
import os
import re
import sys
import urllib.parse
import webbrowser
from threading import Timer

from dotenv import load_dotenv
from flask import Flask, render_template, request

# Load environment variables from .env file
load_dotenv()

# Read strictly from environment
OPERATORS_GROUP = os.getenv("OPERATORS_GROUP")
CSS_PROD = os.getenv("CSS_PROD")

# Sanity check to prevent running without environment variables configured
if not OPERATORS_GROUP or not CSS_PROD:
    raise RuntimeError("OPERATORS_GROUP and CSS_PROD must be defined in your .env file.")


def resource_path(relative_path):
    """Return the correct path for normal Python or a PyInstaller build."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)

MAX_EMAIL_HISTORY = 50


HISTORY_FOLDER = os.path.join(
    os.getenv("APPDATA", os.path.expanduser("~")), "Job Failure Escalator"
)
HISTORY_FILE = os.path.join(HISTORY_FOLDER, "email_history.json")

LOG_FOLDER = os.path.join(HISTORY_FOLDER, "logs")
LOG_FILE = os.path.join(LOG_FOLDER, "escalate.log")

os.makedirs(LOG_FOLDER, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
)

logger = logging.getLogger(__name__)


def load_email_history():
    """Load previously used on-call email addresses."""
    try:
        if not os.path.exists(HISTORY_FILE):
            return []
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            history = json.load(file)
        if isinstance(history, list):
            return [x for x in history if isinstance(x, str)][
                :MAX_EMAIL_HISTORY
            ]
    except (OSError, json.JSONDecodeError):
        pass
    return []


def save_email_history(email):
    """Save an email address as the most recently used address."""
    email = email.strip()
    if not email:
        return
    history = [
        saved
        for saved in load_email_history()
        if saved.lower() != email.lower()
    ]
    history.insert(0, email)
    history = history[:MAX_EMAIL_HISTORY]
    try:
        os.makedirs(HISTORY_FOLDER, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=4)
    except OSError:
        pass


def valid_email(value):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value or ""))


@app.route("/", methods=["GET", "POST"])
def index():
    history = load_email_history()
    error = None
    result = None

    if request.method == "POST":
        logger.info("Escalation form submitted")
        email_choice = request.form.get("email_choice", "").strip()
        new_email = request.form.get("on_call_email", "").strip()

        if email_choice == "__new__":
            on_call_email = new_email
        elif email_choice:
            try:
                on_call_email = history[int(email_choice)]
            except (ValueError, IndexError):
                on_call_email = ""
        else:
            on_call_email = new_email

        job_name = request.form.get("job_name", "").strip()
        scheme_name = request.form.get("scheme_name", "").strip()
        sheet_name = request.form.get("sheet_name", "").strip()
        shift = request.form.get("shift", "").strip()

        if not valid_email(on_call_email):
            error = "Enter a valid on-call email address."
            logger.warning("Escalation rejected: invalid email address")
        elif not job_name or not scheme_name or not sheet_name:
            error = "Please complete the job, scheme, and sheet fields."
            logger.warning("Escalation rejected: incomplete job details")
        elif shift not in ("1", "2"):
            error = "Choose either Day Shift or Night Shift."
            logger.warning("Escalation rejected: invalid shift")
        else:
            save_email_history(on_call_email)
            cc_list = (
                f"{OPERATORS_GROUP};{CSS_PROD}"
                if shift == "1"
                else OPERATORS_GROUP
            )
            shift_name = "Day Shift" if shift == "1" else "Night Shift"
            subject = f"Job Failure Escalation | {job_name.upper()}"
            body = (
                "Hi,\n\n"
                f"As discussed, Please note {job_name.upper()} failed in "
                f"{scheme_name.upper()} {sheet_name.upper()} Runsheet.\n\n"
                "Kind Regards,\n"
            )
            params = {"subject": subject, "body": body, "cc": cc_list}
            mailto_url = (
                f"mailto:{urllib.parse.quote(on_call_email)}?"
                f"{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
            )
            result = {
                "to": on_call_email,
                "cc": cc_list,
                "subject": subject,
                "body": body,
                "shift": shift_name,
                "mailto_url": mailto_url,
            }

            logger.info(
                "Escalation prepared | job=%s | shift=%s | recipient=%s",
                job_name,
                shift_name,
                on_call_email,
            )

            history = load_email_history()

    return render_template(
        "index.html", history=history, error=error, result=result
    )


@app.route("/shutdown", methods=["POST"])
def shutdown():
    logger.info("Job Failure Escalator session ended by user")
    Timer(0.2, lambda: os._exit(0)).start()
    return "Session ended."


if __name__ == "__main__":
    url = "http://localhost:5000"

    logger.info("Job Failure Escalator starting")
    logger.info("Log file: %s", LOG_FILE)

    Timer(1.5, lambda: webbrowser.open_new(url)).start()

    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)