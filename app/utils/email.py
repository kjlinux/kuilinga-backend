import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

def send_email(to_email: str, subject: str, message: str):
    msg = MIMEMultipart()
    msg['From'] = settings.EMAILS_FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.starttls()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        text = msg.as_string()
        server.sendmail(settings.EMAILS_FROM_EMAIL, to_email, text)
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

def send_new_user_email(to_email: str, token: str):
    subject = "Bienvenue chez KUILINGA"
    # Note: L'URL du frontend doit être configurable
    link = f"http://localhost:3000/set-password?token={token}"
    message = f"Votre compte a été créé. Veuillez définir votre mot de passe en cliquant sur le lien suivant : {link}"
    send_email(to_email, subject, message)
