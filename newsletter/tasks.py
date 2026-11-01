from celery import shared_task
from django.utils import timezone
from django.conf import settings
from config.email import send_smtp_mail


def wrap_newsletter_html(content, subject="Isezerano Dispatch"):
    """Wraps campaign content in a modern, responsive email container."""
    if "<html" in content.lower() and "<body" in content.lower():
        return content

    sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'notification@isezerano.com')
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        f'<title>{subject}</title></head>'
        '<body style="margin: 0; padding: 0; background-color: #f3f4f6; '
        'font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif;">'
        '<div style="max-width: 640px; margin: 30px auto; background-color: #ffffff; '
        'border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">'
        '<div style="background-color: #1e3a8a; padding: 24px; text-align: center; border-bottom: 3px solid #3b82f6;">'
        '<h1 style="color: #ffffff; margin: 0; font-size: 26px; font-weight: 900;">ISEZERANO</h1>'
        '<p style="color: #93c5fd; font-size: 11px; margin: 6px 0 0 0; text-transform: uppercase; '
        'letter-spacing: 1.5px; font-family: monospace;">Digital Journalism Platform</p></div>'
        f'<div style="padding: 32px 28px; color: #1f2937; font-size: 15px; line-height: 1.7;">{content}</div>'
        '<div style="background-color: #f9fafb; padding: 20px 24px; text-align: center; '
        'border-top: 1px solid #e5e7eb; font-size: 11px; color: #6b7280; font-family: monospace;">'
        '<p style="margin: 0 0 6px 0;">You are receiving this edition because you subscribed to Isezerano.com.</p>'
        f'<p style="margin: 0;">(c) Isezerano Newsroom | Contact: {sender_email}</p></div></div></body></html>'
    )


@shared_task
def send_newsletter_campaign_task(campaign_id):
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

    html_payload = wrap_newsletter_html(campaign.body, campaign.subject)

    for email in emails:
        try:
            send_smtp_mail(
                subject=campaign.subject,
                message=campaign.body,
                html_message=html_payload,
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


@shared_task
def send_subscription_confirmation(email):
    """Welcome email after newsletter subscribe (queued via Celery)."""
    subject = 'Welcome to Isezerano Newsletter'
    text_body = (
        'Hello,\n\n'
        'Thank you for subscribing to Isezerano.\n\n'
        'You will receive morning editions, daily editorial updates, and breaking coverage in your inbox.\n\n'
        '— The Isezerano Newsroom Team'
    )
    html_body = wrap_newsletter_html(
        f'<h2 style="color: #1e3a8a; margin-top: 0; font-size: 20px;">Muraho! Welcome to Isezerano.</h2>'
        f'<p>Thank you for subscribing to <strong>Isezerano</strong> with your email <code>{email}</code>.</p>'
        '<p>You have joined our verified readers network. You will now receive:</p>'
        '<ul style="padding-left: 20px; line-height: 1.8;">'
        '<li><strong>Morning Briefings:</strong> Essential political, economic, and cultural developments.</li>'
        '<li><strong>Investigative Reporting:</strong> Deep editorial dives and unbiased journalism.</li>'
        '<li><strong>Breaking Alerts:</strong> Timely reporting on major domestic and global events.</li>'
        '</ul>'
        '<p style="margin-top: 24px;">Stay informed with transparent and reliable journalism.</p>'
        '<p style="margin-bottom: 0;">— <em>The Isezerano Editorial Desk</em></p>',
        subject,
    )

    send_smtp_mail(
        subject=subject,
        message=text_body,
        html_message=html_body,
        recipient_list=[email],
    )


@shared_task
def send_ad_kit_request(name, email, company='', message='', phone=''):
    """Notify the ads team and acknowledge the requester via SMTP (queued via Celery)."""
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
    ack_html = wrap_newsletter_html(
        f'<h2 style="color: #1e3a8a; margin-top: 0; font-size: 20px;">Thank You for Your Advertising Inquiry</h2>'
        f'<p>Hi <strong>{name}</strong>,</p>'
        '<p>Thanks for your interest in partnering with <strong>Isezerano</strong>.</p>'
        '<p>Our commercial desk has received your request and is preparing your tailored media rate card.</p>'
        '<p>A member of our team will be in touch with you shortly.</p>'
        '<p style="margin-top: 24px; margin-bottom: 0;">— <em>Isezerano Commercial Desk</em></p>',
        ack_subject,
    )

    send_smtp_mail(
        subject=ack_subject,
        message=ack_text,
        html_message=ack_html,
        recipient_list=[email],
    )
