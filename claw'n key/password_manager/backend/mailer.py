"""
mailer.py
Sends feedback submissions via Gmail SMTP.
Fails silently so the app still works if there's no internet.
"""

import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SENDER   = "teamnibble1234@gmail.com"
SMTP_PASSWORD = "fzau ishg mzku eosi"
SMTP_RECEIVER = "teamnibble1234@gmail.com"


def send_feedback_email(fb_type: str, title: str, content: str):
    """
    Send a feedback submission via Gmail SMTP.
    Runs in a background thread so it never blocks the UI.
    Fails silently if anything goes wrong.
    """
    def _send():
        try:
            subject = f"[Claw'n Key] {fb_type.upper()}: {title or '(no title)'}"

            body = f"""
New feedback from Claw'n Key.

Type:    {fb_type}
Title:   {title or '(none)'}

--- Message ---
{content}
"""
            msg = MIMEMultipart()
            msg["From"] = SMTP_SENDER
            msg["To"] = SMTP_RECEIVER
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(SMTP_SENDER, SMTP_PASSWORD)
                server.sendmail(SMTP_SENDER, SMTP_RECEIVER, msg.as_string())

            print("[Mailer] Feedback sent.")

        except Exception as e:
            print(f"[Mailer] Failed to send (continuing anyway): {e}")

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()