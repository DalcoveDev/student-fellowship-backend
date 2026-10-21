from rest_framework import serializers
from .models import MediaAsset


class MediaAssetSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = MediaAsset
        fields = ('id', 'file', 'file_url', 'title', 'caption', 'alt_text', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at')

    def get_file_url(self, obj):
        if not obj.file:
            return None
        name = obj.file.name
        if name.startswith('http://') or name.startswith('https://'):
            return name
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url
