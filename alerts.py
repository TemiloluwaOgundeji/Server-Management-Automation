#!/usr/bin/env python3
"""
Email + Slack alert script
"""

import os
import smtplib
import requests
from email.message import EmailMessage


# CONFIGURATION
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "zinaanjolaiya@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "raoo rjhr cbjp ngjy")
EMAIL_FROM = os.getenv("EMAIL_FROM", "zinaanjolaiya@gmail.com")
EMAIL_TO = os.getenv("EMAIL_TO", "togundeji50@gmail.com").split(",")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/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")


# ALERT FUNCTIONS
def send_email(subject, message):
    """Send email alert"""
    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_TO)
    msg["Subject"] = subject
    msg.set_content(message)

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, 465) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        print("Email alert sent")
    except Exception as e:
        print(f"Email send failed: {e}")

def send_slack(subject, message, level):
    """Send Slack webhook alert"""
    payload = {
        "text": f"*{level.upper()} ALERT*: {subject}\n{message}"
    }
    try:
        r = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if r.status_code == 200:
            print("Slack alert sent")
        else:
            print(f"Slack send failed ({r.status_code}): {r.text}")
    except Exception as e:
        print(f"Slack send failed: {e}")

def send_alert(level, subject, message):
    """Send alert to both Email and Slack"""
    formatted_subject = f"[{level.upper()}] {subject}"
    send_email(formatted_subject, message)
    send_slack(subject, message, level)


# EXAMPLE INTEGRATION
def example_check():
    """Simulate a system check that fails"""
    return False  # change to True to simulate success

def main():
    if not example_check():
        send_alert(
            level="high",
            subject="Server Check Failed",
            message="The example system check returned False."
        )

if __name__ == "__main__":
    main()
