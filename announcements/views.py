from django.db.models import Q
from rest_framework import viewsets, generics, permissions

from .models import Announcement
from .serializers import AnnouncementSerializer
from users.permissions import IsEditor


class PublicAnnouncementListView(generics.ListAPIView):
    serializer_class = AnnouncementSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = Announcement.objects.filter(is_active=True)

        # Filter by type
        announcement_type = self.request.query_params.get('type')
        if announcement_type:
            queryset = queryset.filter(announcement_type=announcement_type)

        # Search by title or organization name (fixed OR logic)
        search_query = self.request.query_params.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | Q(organization_name__icontains=search_query)
            )

        return queryset


class PublicAnnouncementDetailView(generics.RetrieveAPIView):
    queryset = Announcement.objects.filter(is_active=True)
    serializer_class = AnnouncementSerializer
    permission_classes = (permissions.AllowAny,)
    lookup_field = 'pk'


# ================= CMS API VIEWS =================

class CMSAnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = (IsEditor,)
