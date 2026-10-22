import logging

from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Subscriber, NewsletterCampaign
from .serializers import SubscriberSerializer, NewsletterCampaignSerializer
from .tasks import (
    send_newsletter_campaign_task,
    send_subscription_confirmation,
    wrap_newsletter_html,
)
from users.permissions import IsEditor, IsAdmin

logger = logging.getLogger(__name__)


class SubscribeView(generics.CreateAPIView):
    queryset = Subscriber.objects.all()
    serializer_class = SubscriberSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        # Allow activating an existing inactive subscriber
        email = request.data.get('email')
        if email:
            email = email.strip().lower()
            subscriber, created = Subscriber.objects.get_or_create(email=email)
            if not created and not subscriber.is_active:
                subscriber.is_active = True
                subscriber.save()
            try:
                send_subscription_confirmation.delay(email)
            except Exception:
                try:
                    send_subscription_confirmation(email)
                except Exception as exc:
                    logger.exception("Newsletter confirmation email failed for %s: %s", email, exc)
            serializer = self.get_serializer(subscriber)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'email': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)


# ================= CMS API VIEWS =================

class CMSSubscriberViewSet(viewsets.ModelViewSet):
    queryset = Subscriber.objects.all().order_by('-subscribed_at')
    serializer_class = SubscriberSerializer
    permission_classes = (IsEditor,)


class CMSNewsletterCampaignViewSet(viewsets.ModelViewSet):
    queryset = NewsletterCampaign.objects.all().order_by('-created_at')
    serializer_class = NewsletterCampaignSerializer
    permission_classes = (IsAdmin,)

    @action(detail=True, methods=['post'])
    def send_campaign(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status == 'sent':
            return Response({'detail': 'Campaign was already sent.'}, status=status.HTTP_400_BAD_REQUEST)

        # Prefer async Celery; fall back to synchronous send if broker is unavailable
        try:
            send_newsletter_campaign_task.delay(campaign.id)
            return Response(
                {'status': 'Campaign queued for transmission to all active subscribers.'},
                status=status.HTTP_200_OK,
            )
        except Exception:
            result = send_newsletter_campaign_task(campaign.id)
            return Response({'status': result}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def test_send(self, request, pk=None):
        """Sends a one-off preview email of the campaign to a single test recipient."""
        campaign = self.get_object()
        test_email = (request.data.get('email') or '').strip() or getattr(request.user, 'email', '')
        if not test_email:
            return Response(
                {'detail': 'Recipient email is required for test send.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from config.email import send_smtp_mail
        html_payload = wrap_newsletter_html(campaign.body, f"[TEST PREVIEW] {campaign.subject}")
        try:
            send_smtp_mail(
                subject=f"[TEST PREVIEW] {campaign.subject}",
                message=campaign.body,
                html_message=html_payload,
                recipient_list=[test_email],
            )
            return Response(
                {'status': f'Test preview email dispatched to {test_email}'},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            logger.exception("Test send failed for campaign %s to %s", campaign.id, test_email)
            return Response({'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
