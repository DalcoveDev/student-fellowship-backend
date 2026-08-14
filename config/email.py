"""Shared SMTP helpers for all outbound email."""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail


def send_smtp_mail(
    subject,
    message,
    recipient_list,
    html_message=None,
    from_email=None,
    fail_silently=False,
):
    """Send email via the configured SMTP backend."""
    sender = from_email or settings.DEFAULT_FROM_EMAIL
    recipients = [email for email in recipient_list if email]

    if not recipients:
        raise ValueError('At least one recipient email is required.')

    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        raise RuntimeError('SMTP credentials are not configured.')

    if html_message:
        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=sender,
            to=recipients,
        )
        email.attach_alternative(html_message, 'text/html')
        return email.send(fail_silently=fail_silently)

    return send_mail(
        subject=subject,
        message=message,
        from_email=sender,
        recipient_list=recipients,
        fail_silently=fail_silently,
    )
