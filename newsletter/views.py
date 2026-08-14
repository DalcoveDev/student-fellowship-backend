import logging

from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from .models import Subscriber, NewsletterCampaign
from .serializers import SubscriberSerializer, NewsletterCampaignSerializer
from .tasks import (
    send_newsletter_campaign_task,
    send_subscription_confirmation,
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
            subscriber, created = Subscriber.objects.get_or_create(email=email)
            if not created:
                subscriber.is_active = True
                subscriber.save()
            try:
                send_subscription_confirmation(email)
            except Exception:
                logger.exception("Newsletter confirmation email failed for %s", email)
            serializer = self.get_serializer(subscriber)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'email': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)


# ================= CMS API VIEWS =================

class CMSSubscriberViewSet(viewsets.ModelViewSet):
    queryset = Subscriber.objects.all()
    serializer_class = SubscriberSerializer
    permission_classes = (IsEditor,)


class CMSNewsletterCampaignViewSet(viewsets.ModelViewSet):
    queryset = NewsletterCampaign.objects.all()
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
            return Response({'status': 'Campaign queued for sending'}, status=status.HTTP_200_OK)
        except Exception:
            result = send_newsletter_campaign_task(campaign.id)
            return Response({'status': result}, status=status.HTTP_200_OK)
