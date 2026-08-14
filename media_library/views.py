from rest_framework import viewsets, filters
from .models import MediaAsset
from .serializers import MediaAssetSerializer
from users.permissions import IsJournalist

class CMSMediaAssetViewSet(viewsets.ModelViewSet):
    queryset = MediaAsset.objects.all().order_by('-uploaded_at')
    serializer_class = MediaAssetSerializer
    permission_classes = (IsJournalist,)
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'caption', 'alt_text']
