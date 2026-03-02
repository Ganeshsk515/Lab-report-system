import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(subject, recipients, body):
    mail_server = current_app.config.get("MAIL_SERVER")
    mail_from = current_app.config.get("MAIL_FROM")
    if not mail_server or not mail_from:
        current_app.logger.warning(
            "Email not sent because MAIL_SERVER or MAIL_FROM is not configured. Subject: %s",
            subject,
        )
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = mail_from
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    try:
        mail_port = int(current_app.config.get("MAIL_PORT", 587))
        use_ssl = bool(current_app.config.get("MAIL_USE_SSL", False))
        use_tls = bool(current_app.config.get("MAIL_USE_TLS", True))

        if use_ssl:
            server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=15)
        else:
            server = smtplib.SMTP(mail_server, mail_port, timeout=15)

        with server:
            if use_tls and not use_ssl:
                server.starttls()

            username = current_app.config.get("MAIL_USERNAME")
            password = current_app.config.get("MAIL_PASSWORD")
            if username and password:
                server.login(username, password)

            server.send_message(message)

        return True
    except Exception as exc:
        current_app.logger.error("Email send failed for %s: %s", recipients, exc)
        return False
