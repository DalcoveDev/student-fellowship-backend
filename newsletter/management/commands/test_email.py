"""Management command to test email delivery via Mailjet."""
from django.core.management.base import BaseCommand
from django.conf import settings
from config.email import send_smtp_mail, send_via_mailjet_api


class Command(BaseCommand):
    help = "Test email sending via Mailjet SMTP and API."

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            nargs='?',
            default='notification@isezerano.com',
            help='Recipient email address (defaults to notification@isezerano.com)',
        )
        parser.add_argument(
            '--api-only',
            action='store_true',
            help='Send strictly using the Mailjet REST API v3.1',
        )

    def handle(self, *args, **options):
        recipient = options['recipient']
        api_only = options['api_only']

        self.stdout.write(self.style.NOTICE("=================================================="))
        self.stdout.write(self.style.NOTICE("        ISEZERANO MAILJET EMAIL TEST             "))
        self.stdout.write(self.style.NOTICE("=================================================="))
        self.stdout.write(f"From Address: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"To Address:   {recipient}")
        self.stdout.write(f"SMTP Host:    {settings.EMAIL_HOST}:{settings.EMAIL_PORT} (TLS={settings.EMAIL_USE_TLS})")
        api_key_mask = (
            f"{settings.MAILJET_API_KEY[:6]}...{settings.MAILJET_API_KEY[-4:]}"
            if settings.MAILJET_API_KEY else 'NONE'
        )
        self.stdout.write(f"API Key:      {api_key_mask}")
        self.stdout.write("--------------------------------------------------")

        subject = "Isezerano — Mailjet Email System Verification"
        text_body = (
            "Hello,\n\n"
            "This is a verified test email sent from the Isezerano digital journalism platform "
            f"using Mailjet outbound delivery via {settings.DEFAULT_FROM_EMAIL}.\n\n"
            "If you are receiving this message, the email pipeline is working perfectly.\n\n"
            "— Isezerano Tech Team"
        )
        html_body = (
            '<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; '
            'padding: 24px; border: 1px solid #e5e7eb; border-radius: 8px;">\n'
            '  <div style="text-align: center; margin-bottom: 24px;">\n'
            '    <h1 style="color: #2563eb; margin: 0; font-size: 26px;">ISEZERANO</h1>\n'
            '    <p style="color: #6b7280; font-size: 12px; margin-top: 4px; text-transform: uppercase;">\n'
            '      Digital Journalism Platform\n'
            '    </p>\n'
            '  </div>\n'
            '  <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; '
            'border-radius: 6px; padding: 16px; margin-bottom: 20px;">\n'
            '    <h3 style="color: #166534; margin: 0 0 8px 0; font-size: 16px;">[SUCCESS] Mailjet Delivery</h3>\n'
            f'    <p style="color: #15803d; font-size: 14px; margin: 0; line-height: 1.5;">\n'
            f'      Email dispatched from <strong>{settings.DEFAULT_FROM_EMAIL}</strong> to '
            f'<strong>{recipient}</strong>.\n'
            '    </p>\n'
            '  </div>\n'
            '  <p style="color: #374151; font-size: 14px; line-height: 1.6;">\n'
            '    The outbound email pipeline for newsletters, ad inquiries, and system notifications '
            'is fully operational.\n'
            '  </p>\n'
            '  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />\n'
            f'  <p style="color: #9ca3af; font-size: 11px; text-align: center; margin: 0;">\n'
            f'    (c) {settings.DEFAULT_FROM_EMAIL} — Isezerano Newsroom\n'
            '  </p>\n'
            '</div>'
        )

        try:
            if api_only:
                self.stdout.write("Sending via Mailjet API v3.1...")
                result = send_via_mailjet_api(
                    subject=subject,
                    message=text_body,
                    recipient_list=[recipient],
                    html_message=html_body,
                )
                self.stdout.write(self.style.SUCCESS("[SUCCESS] Mailjet API delivery succeeded!"))
                self.stdout.write(f"Response: {result}")
            else:
                self.stdout.write("Sending via SMTP (with automatic Mailjet API fallback)...")
                send_smtp_mail(
                    subject=subject,
                    message=text_body,
                    recipient_list=[recipient],
                    html_message=html_body,
                )
                self.stdout.write(self.style.SUCCESS(f"[SUCCESS] Email successfully dispatched to {recipient}!"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"[ERROR] Delivery failed: {exc}"))
            raise exc
