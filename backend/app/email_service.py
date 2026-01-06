import smtplib
from email.mime.text import MIMEText

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "YOUR_GMAIL@gmail.com"
SMTP_PASSWORD = "YOUR_GMAIL_APP_PASSWORD"  # NOT your normal password

def send_invitation_email(to_email, invite_link):
    subject = "You're invited to join the platform"
    body = f"""
    Hello,

    You have been invited to join our platform.

    Please click the link below to set your password and activate your account:

    {invite_link}

    This link expires in 7 days.

    Regards,
    Admin Team
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_EMAIL, SMTP_PASSWORD)
    server.send_message(msg)
    server.quit()
