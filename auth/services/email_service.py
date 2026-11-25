import os
import smtplib
import ssl
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "rnani7046@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "cqxazaamjkkdxwhb").replace(" ", "")
EMAILS_FROM_NAME = os.getenv("EMAILS_FROM_NAME", "AI Interview Platform")


def send_otp_email(recipient_email: str, otp_code: str, user_name: str = "Candidate"):
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[WARNING] SMTP credentials missing. OTP email not sent.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your Verification OTP: {otp_code}"
    msg["From"] = f"{EMAILS_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = recipient_email

    text_content = f"Hello {user_name},\n\nYour OTP is: {otp_code}\nExpires in 10 minutes."
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background: #f8fafc;">
      <div style="max-width: 440px; margin: 0 auto; background: #fff; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0;">
        <h3 style="color: #0f172a; margin-top: 0;">Verification Code</h3>
        <p>Hello <strong>{user_name}</strong>,</p>
        <p>Use the code below to complete verification:</p>
        <div style="background: #f1f5f9; padding: 14px; text-align: center; font-size: 26px; font-weight: bold; letter-spacing: 5px; color: #2563eb; border-radius: 6px;">
          {otp_code}
        </div>
        <p style="color: #64748b; font-size: 13px; margin-top: 14px;">Valid for 10 minutes.</p>
      </div>
    </div>
    """

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    def _worker():
        # 1. Check for HTTPS Email API if configured (works across all cloud platforms)
        resend_key = os.getenv("RESEND_API_KEY", "").strip()
        if resend_key:
            try:
                import urllib.request
                import json
                payload = {
                    "from": f"{EMAILS_FROM_NAME} <onboarding@resend.dev>",
                    "to": [recipient_email],
                    "subject": f"Your Verification OTP: {otp_code}",
                    "html": html_content,
                }
                req = urllib.request.Request(
                    "https://api.resend.com/emails",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {resend_key}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    print(f"[HTTPS DISPATCH SUCCESS] Delivered OTP via Resend to {recipient_email} ({resp.status})")
                    return
            except Exception as e_res:
                print(f"[HTTPS DISPATCH NOTICE] Resend OTP attempt failed: {e_res}")

        # 2. Try Direct SSL on Port 465
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, 465, context=context, timeout=8) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, recipient_email, msg.as_string())
            print(f"[EMAIL SUCCESS] Dispatched OTP (via SSL 465) to {recipient_email}")
            return
        except Exception as exc_ssl:
            print(f"[EMAIL 465 NOTICE] Port 465 failed ({exc_ssl}), trying Port 587 (TLS)...")

        # 3. Try Port 587 (STARTTLS)
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_HOST, 587, timeout=8) as server:
                server.starttls(context=context)
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, recipient_email, msg.as_string())
            print(f"[EMAIL SUCCESS] Dispatched OTP (via TLS 587) to {recipient_email}")
            return
        except Exception as exc_tls:
            print(f"[EMAIL ERROR] Both SMTP ports 465 and 587 failed to {recipient_email}: {exc_tls}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
