import smtplib
from email.message import EmailMessage
from app.core.config import settings
def send_password_reset_email(email: str, token: str):
    if not settings.smtp_host:
        print(f"[DEV] Password reset URL for {email}: {settings.frontend_url}/reset-password?token={token}")
        return
    msg=EmailMessage(); msg['Subject']='Mukando password reset'; msg['From']=settings.smtp_from; msg['To']=email
    msg.set_content(f"Reset your Mukando password using this link: {settings.frontend_url}/reset-password?token={token}")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls();
        if settings.smtp_username: server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)
