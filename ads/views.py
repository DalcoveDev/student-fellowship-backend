import logging

from django.db.models import F
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AdSlot
from .serializers import AdSlotSerializer, AnalyticsEventSerializer
from newsletter.tasks import send_ad_kit_request
from users.permissions import IsEditor

logger = logging.getLogger(__name__)


class ActiveAdView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, placement):
        now = timezone.now()
        # Normalise placement: try both hyphen and underscore variants
        candidates = {placement}
        if '-' in placement:
            candidates.add(placement.replace('-', '_'))
        if '_' in placement:
            candidates.add(placement.replace('_', '-'))

        # Primary: active ads whose schedule window is open
        ads = AdSlot.objects.filter(
            placement__in=candidates,
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
        ).order_by('-priority', '-id')

        # Fallback: if no scheduled ad is currently in window, serve the latest active ad
        if not ads.exists():
            ads = AdSlot.objects.filter(
                placement__in=candidates,
                is_active=True,
            ).order_by('-priority', '-id')

        if not ads.exists():
            return Response({'detail': 'No active ads found.'}, status=status.HTTP_404_NOT_FOUND)

        ad = ads.first()
        serializer = AdSlotSerializer(ad, context={'request': request})
        return Response(serializer.data)


class PublicAdSlotDetailView(APIView):
    """Public read endpoint to fetch a specific AdSlot by ID."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request, pk):
        try:
            ad = AdSlot.objects.get(pk=pk, is_active=True)
            serializer = AdSlotSerializer(ad, context={'request': request})
            return Response(serializer.data)
        except AdSlot.DoesNotExist:
            return Response({'detail': 'Ad slot not found or inactive.'}, status=status.HTTP_404_NOT_FOUND)


class RequestAdKitView(APIView):
    """Public endpoint: send ad kit inquiry + acknowledgement via SMTP."""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        name = (request.data.get('name') or '').strip()
        email = (request.data.get('email') or '').strip()
        company = (request.data.get('company') or '').strip()
        phone = (request.data.get('phone') or '').strip()
        message = (request.data.get('message') or '').strip()

        if not name or not email:
            return Response(
                {'detail': 'Name and email are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            try:
                send_ad_kit_request.delay(
                    name=name,
                    email=email,
                    company=company,
                    phone=phone,
                    message=message,
                )
            except Exception:
                send_ad_kit_request(
                    name=name,
                    email=email,
                    company=company,
                    phone=phone,
                    message=message,
                )
        except Exception:
            logger.exception("Ad kit email failed for %s <%s>", name, email)
            return Response(
                {'detail': 'Unable to process your request. Please try again later.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {'status': 'Ad kit request sent successfully.'},
            status=status.HTTP_200_OK,
        )


class TrackAnalyticsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = AnalyticsEventSerializer(data=request.data)
        if serializer.is_valid():
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            referrer = request.META.get('HTTP_REFERER', '')

            event = serializer.save(
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
            )

            # Accumulate totals in the AdSlot atomically
            if event.ad_slot:
                if event.event_type == 'ad_impression':
                    AdSlot.objects.filter(id=event.ad_slot_id).update(impressions=F('impressions') + 1)
                elif event.event_type == 'ad_click':
                    AdSlot.objects.filter(id=event.ad_slot_id).update(clicks=F('clicks') + 1)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ================= CMS API VIEWS =================

class CMSAdSlotViewSet(viewsets.ModelViewSet):
    queryset = AdSlot.objects.all().order_by('-priority', 'id')
    serializer_class = AdSlotSerializer
    permission_classes = (IsEditor,)
    pagination_class = None

    @action(detail=True, methods=['post', 'patch'], url_path='toggle-description')
    def toggle_description(self, request, pk=None):
        ad = self.get_object()
        if 'show_description' in request.data:
            val = request.data.get('show_description')
            ad.show_description = str(val).lower() in ('true', '1') if isinstance(val, str) else bool(val)
        else:
            ad.show_description = not ad.show_description
        ad.save(update_fields=['show_description'])
        return Response(self.get_serializer(ad).data)
