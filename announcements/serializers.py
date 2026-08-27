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

    def to_representation(self, instance):
        if hasattr(instance, 'published_date') and instance.published_date and hasattr(instance.published_date, 'date'):
            instance.published_date = instance.published_date.date()
        if hasattr(instance, 'deadline_date') and instance.deadline_date and hasattr(instance.deadline_date, 'date'):
            instance.deadline_date = instance.deadline_date.date()
        return super().to_representation(instance)
