"""Shared SMTP & Mailjet helpers for all outbound email."""
import logging
import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail

logger = logging.getLogger(__name__)


def send_via_mailjet_api(
    subject,
    message,
    recipient_list,
    html_message=None,
    from_email=None,
):
    """Direct sending via Mailjet v3.1 Send API."""
    api_key = getattr(settings, 'MAILJET_API_KEY', None)
    secret_key = getattr(settings, 'MAILJET_SECRET_KEY', None)
    if not api_key or not secret_key:
        raise RuntimeError('Mailjet API credentials are not configured.')

    sender = from_email or settings.DEFAULT_FROM_EMAIL
    messages = []
    for recipient in recipient_list:
        msg = {
            "From": {
                "Email": sender,
                "Name": "Isezerano"
            },
            "To": [
                {
                    "Email": recipient
                }
            ],
            "Subject": subject,
            "TextPart": message,
        }
        if html_message:
            msg["HTMLPart"] = html_message
        messages.append(msg)

    timeout = getattr(settings, 'EMAIL_TIMEOUT', 20)
    response = requests.post(
        "https://api.mailjet.com/v3.1/send",
        auth=(api_key, secret_key),
        json={"Messages": messages},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def send_smtp_mail(
    subject,
    message,
    recipient_list,
    html_message=None,
    from_email=None,
    fail_silently=False,
):
    """Send email via the configured SMTP backend with Mailjet API fallback."""
    sender = from_email or settings.DEFAULT_FROM_EMAIL
    recipients = [email for email in recipient_list if email]

    if not recipients:
        raise ValueError('At least one recipient email is required.')

    # Try standard Django SMTP backend first if host user/password are configured
    if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
        try:
            if html_message:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=sender,
                    to=recipients,
                )
                email.attach_alternative(html_message, 'text/html')
                return email.send(fail_silently=False)

            return send_mail(
                subject=subject,
                message=message,
                from_email=sender,
                recipient_list=recipients,
                fail_silently=False,
            )
        except Exception as smtp_err:
            logger.warning("SMTP transmission error (%s), attempting Mailjet API fallback...", smtp_err)
            if getattr(settings, 'MAILJET_API_KEY', None) and getattr(settings, 'MAILJET_SECRET_KEY', None):
                try:
                    return send_via_mailjet_api(
                        subject=subject,
                        message=message,
                        recipient_list=recipients,
                        html_message=html_message,
                        from_email=sender,
                    )
                except Exception as api_err:
                    logger.error("Mailjet API fallback also failed: %s", api_err)
                    if not fail_silently:
                        raise api_err
            if not fail_silently:
                raise smtp_err

    # Fall back directly to Mailjet API if SMTP username/password are omitted
    if getattr(settings, 'MAILJET_API_KEY', None) and getattr(settings, 'MAILJET_SECRET_KEY', None):
        try:
            return send_via_mailjet_api(
                subject=subject,
                message=message,
                recipient_list=recipients,
                html_message=html_message,
                from_email=sender,
            )
        except Exception as api_err:
            logger.error("Mailjet API send failed: %s", api_err)
            if not fail_silently:
                raise api_err
            return None

    if not fail_silently:
        raise RuntimeError('Neither SMTP credentials nor Mailjet API credentials are configured.')
