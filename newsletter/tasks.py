from celery import shared_task
from django.utils import timezone
from django.conf import settings
from config.email import send_smtp_mail


@shared_task
def send_newsletter_campaign_task(campaign_id):
    # Move model imports inside the task function to prevent premature app registry checks
    from .models import Subscriber, NewsletterCampaign

    try:
        campaign = NewsletterCampaign.objects.get(id=campaign_id)
    except NewsletterCampaign.DoesNotExist:
        return f"Campaign {campaign_id} not found."

    if campaign.status == 'sent':
        return f"Campaign {campaign_id} has already been sent."

    campaign.status = 'sending'
    campaign.save(update_fields=['status'])

    active_subscribers = Subscriber.objects.filter(is_active=True)
    emails = [sub.email for sub in active_subscribers]
    sent_count = 0
    errors = []

    for email in emails:
        try:
            send_smtp_mail(
                subject=campaign.subject,
                message=campaign.body,
                html_message=campaign.body,
                recipient_list=[email],
            )
            sent_count += 1
        except Exception as exc:
            errors.append(f"{email}: {exc}")

    campaign.status = 'sent'
    campaign.sent_at = timezone.now()
    campaign.save(update_fields=['status', 'sent_at'])

    if errors:
        return (
            f"Campaign '{campaign.subject}' sent to {sent_count}/{len(emails)} "
            f"subscribers with {len(errors)} error(s)."
        )

    return f"Campaign '{campaign.subject}' successfully transmitted to {sent_count} subscribers."


def send_subscription_confirmation(email):
    """Welcome email after newsletter subscribe."""
    subject = 'Welcome to Isezerano'
    text_body = (
        'Thank you for subscribing to Isezerano.\n\n'
        'You will receive morning editions and daily editorial updates.\n\n'
        '— The Isezerano Team'
    )
    html_body = (
        '<p>Thank you for subscribing to <strong>Isezerano</strong>.</p>'
        '<p>You will receive morning editions and daily editorial updates.</p>'
        '<p>— The Isezerano Team</p>'
    )
    send_smtp_mail(
        subject=subject,
        message=text_body,
        html_message=html_body,
        recipient_list=[email],
    )


def send_ad_kit_request(*, name, email, company='', message='', phone=''):
    """Notify the ads team and acknowledge the requester via SMTP."""
    ads_inbox = getattr(settings, 'ADS_INQUIRY_EMAIL', None) or settings.DEFAULT_FROM_EMAIL

    internal_subject = f'Ad Kit Request from {name}'
    internal_body = (
        f'New advertising inquiry\n\n'
        f'Name: {name}\n'
        f'Email: {email}\n'
        f'Company: {company or "—"}\n'
        f'Phone: {phone or "—"}\n\n'
        f'Message:\n{message or "(no message)"}\n'
    )
    send_smtp_mail(
        subject=internal_subject,
        message=internal_body,
        recipient_list=[ads_inbox],
    )

    ack_subject = 'Your Isezerano Ad Kit Request'
    ack_text = (
        f'Hi {name},\n\n'
        'Thanks for your interest in advertising on Isezerano. '
        'Our team will send your ad kit shortly.\n\n'
        '— Isezerano Advertising'
    )
    ack_html = (
        f'<p>Hi {name},</p>'
        '<p>Thanks for your interest in advertising on <strong>Isezerano</strong>. '
        'Our team will send your ad kit shortly.</p>'
        '<p>— Isezerano Advertising</p>'
    )
    send_smtp_mail(
        subject=ack_subject,
        message=ack_text,
        html_message=ack_html,
        recipient_list=[email],
    )
