"""Shared SMTP & Mailjet helpers for all outbound email."""
import logging
import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail

logger = logging.getLogger(__name__)


def _get_mailjet_credentials():
    """Return (api_key, secret_key) from settings, falling back to SMTP credentials when Mailjet host is used."""
    api_key = (getattr(settings, 'MAILJET_API_KEY', None) or '').strip()
    secret_key = (getattr(settings, 'MAILJET_SECRET_KEY', None) or '').strip()
    if not api_key or not secret_key:
        email_host = (getattr(settings, 'EMAIL_HOST', None) or '').lower()
        if 'mailjet' in email_host:
            api_key = api_key or (getattr(settings, 'EMAIL_HOST_USER', None) or '').strip()
            secret_key = secret_key or (getattr(settings, 'EMAIL_HOST_PASSWORD', None) or '').strip()
    return api_key, secret_key


def send_via_mailjet_api(
    subject,
    message,
    recipient_list,
    html_message=None,
    from_email=None,
):
    """Direct sending via Mailjet v3.1 Send API over HTTPS (port 443)."""
    api_key, secret_key = _get_mailjet_credentials()
    if not api_key or not secret_key:
        raise RuntimeError('Mailjet API credentials are not configured.')

    sender = (from_email or settings.DEFAULT_FROM_EMAIL or 'notification@isezerano.com').strip()
    if sender == 'noreply@isezerano.com':
        sender = 'notification@isezerano.com'

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

    timeout = min(int(getattr(settings, 'EMAIL_TIMEOUT', 15) or 15), 15)
    response = requests.post(
        "https://api.mailjet.com/v3.1/send",
        auth=(api_key, secret_key),
        json={"Messages": messages},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    for msg_result in payload.get("Messages", []):
        if msg_result.get("Status") == "error":
            errors = msg_result.get("Errors") or []
            err_msg = "; ".join(
                e.get("ErrorMessage", "Unknown Mailjet error") for e in errors
            ) or "Mailjet rejected message"
            raise RuntimeError(f"Mailjet API error: {err_msg}")
    return payload


def _send_via_django_backend(
    subject,
    message,
    recipients,
    sender,
    html_message=None,
):
    """Send via configured Django EMAIL_BACKEND (SMTP or locmem during tests)."""
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


def send_smtp_mail(
    subject,
    message,
    recipient_list,
    html_message=None,
    from_email=None,
    fail_silently=False,
):
    """Send email reliably via Mailjet HTTPS API first (in production) or SMTP backend with fallback."""
    sender = (from_email or settings.DEFAULT_FROM_EMAIL or 'notification@isezerano.com').strip()
    if sender == 'noreply@isezerano.com':
        sender = 'notification@isezerano.com'
    recipients = [email.strip() for email in recipient_list if email and email.strip()]

    if not recipients:
        raise ValueError('At least one recipient email is required.')

    email_backend = getattr(settings, 'EMAIL_BACKEND', '') or ''
    is_test_or_memory_backend = (
        getattr(settings, 'TESTING', False)
        or 'locmem' in email_backend
        or 'console' in email_backend
        or 'filebased' in email_backend
    )

    # 1. In tests or non-network backends, use Django's email backend directly
    if is_test_or_memory_backend:
        try:
            return _send_via_django_backend(subject, message, recipients, sender, html_message)
        except Exception as err:
            if not fail_silently:
                raise err
            return None

    api_key, secret_key = _get_mailjet_credentials()

    # 2. Prefer Mailjet HTTPS API (port 443) when credentials exist so cloud SMTP port blocks never stall requests
    if api_key and secret_key:
        try:
            return send_via_mailjet_api(
                subject=subject,
                message=message,
                recipient_list=recipients,
                html_message=html_message,
                from_email=sender,
            )
        except Exception as api_err:
            logger.warning("Mailjet HTTPS API error (%s), attempting SMTP fallback...", api_err)
            if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
                try:
                    return _send_via_django_backend(subject, message, recipients, sender, html_message)
                except Exception as smtp_err:
                    logger.error("SMTP fallback also failed: %s", smtp_err)
                    if not fail_silently:
                        raise api_err
                    return None
            if not fail_silently:
                raise api_err
            return None

    # 3. Try standard Django SMTP backend if host user/password are configured
    if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
        try:
            return _send_via_django_backend(subject, message, recipients, sender, html_message)
        except Exception as smtp_err:
            logger.error("SMTP transmission error: %s", smtp_err)
            if not fail_silently:
                raise smtp_err
            return None

    if not fail_silently:
        raise RuntimeError('Neither Mailjet API credentials nor SMTP credentials are configured.')
    return None
