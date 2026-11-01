import logging

from django.db.models import F, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
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

        category = (request.query_params.get('category') or '').strip()
        include_all = (request.query_params.get('all') or '').lower() in (
            '1', 'true', 'yes',
        )

        def queryset_for(category_filter):
            qs = AdSlot.objects.filter(
                placement__in=candidates,
                is_active=True,
            )
            if category_filter:
                qs = qs.filter(Q(category__iexact=category_filter) | Q(category=''))
            return qs.order_by('-priority', '-id')

        # Primary: active ads whose schedule window is open.
        ads = list(queryset_for(category).filter(
            start_date__lte=now,
            end_date__gte=now,
        ))
        # Fallback: if no scheduled ad is currently in window, serve active
        # ads anyway so a campaign is never silently hidden by bad dates.
        if not ads:
            ads = list(queryset_for(category))

        # If this category has no specific ad, fall back to any ad in this
        # placement so placements never go blank unnecessarily.
        if not ads and category:
            ads = list(AdSlot.objects.filter(
                placement__in=candidates,
                is_active=True,
            ).order_by('-priority', '-id'))

        if not ads:
            return Response({'detail': 'No active ads found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdSlotSerializer(ads, many=True, context={'request': request})
        if include_all:
            return Response(serializer.data)
        return Response(serializer.data[0])


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
    queryset = AdSlot.objects.all().order_by('category', '-priority', 'id')
    serializer_class = AdSlotSerializer
    permission_classes = (IsEditor,)
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['placement', 'is_active', 'category']
    search_fields = ['name', 'placement', 'category']
    ordering_fields = ['priority', 'name', 'id', 'category']
    ordering = ['category', '-priority', 'id']

    @action(detail=True, methods=['post', 'patch'], url_path='toggle-description')
    def toggle_description(self, request, pk=None):
        """Toggle (or explicitly set) whether an ad displays its description."""
        ad = self.get_object()
        if 'show_description' in request.data:
            val = request.data.get('show_description')
            ad.show_description = str(val).lower() in ('true', '1') if isinstance(val, str) else bool(val)
        else:
            ad.show_description = not ad.show_description
        ad.save(update_fields=['show_description'])
        return Response(self.get_serializer(ad).data)
