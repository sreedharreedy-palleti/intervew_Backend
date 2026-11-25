import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from Resume_Analysis.email_templates import _dispatch_smtp

load_dotenv()

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

    _dispatch_smtp(recipient_email, msg, html_body=html_content, target_name=user_name)
    return True
