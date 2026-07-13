import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


def send_high_match_notification(
    recruiter_email: str,
    candidate_name: str | None,
    job_title: str,
    final_score: float,
    explanation: str,
) -> None:
    """
    Sends an email alert to the recruiter when a resume scores above the
    high-match threshold. Uses plain smtplib — works with Mailhog locally,
    or any real SMTP server (Gmail, SendGrid SMTP relay) in production
    just by changing the .env values.
    """
    name = candidate_name or "A candidate"
    subject = f"High Match Alert: {name} — {final_score}% match for {job_title}"

    body = (
        f"Good news!\n\n"
        f"{name} scored {final_score}% for the job '{job_title}'.\n\n"
        f"Details: {explanation}\n\n"
        f"Log in to SmartHire to review the full profile."
    )

    message = MIMEMultipart()
    message["From"] = settings.FROM_EMAIL
    message["To"] = recruiter_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USER:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.FROM_EMAIL, recruiter_email, message.as_string())
    except Exception as e:
        # Email failure should never break the matching flow — just log it.
        print(f"[email_service] Failed to send notification: {e}")
