from rest_framework import serializers
from .models import Announcement

class AnnouncementSerializer(serializers.ModelSerializer):
    attachment = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = (
            'id', 'title', 'body', 'announcement_type', 'organization_name', 
            'reference_number', 'published_date', 'deadline_date', 'attachment', 'is_active'
        )

    def get_attachment(self, obj):
        if not obj.attachment:
            return None
        name = obj.attachment.name
        if name.startswith('http://') or name.startswith('https://'):
            return name
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.attachment.url)
        return obj.attachment.url
