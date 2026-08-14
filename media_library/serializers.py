from rest_framework import serializers
from .models import MediaAsset

class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = ('id', 'file', 'title', 'caption', 'alt_text', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at')
