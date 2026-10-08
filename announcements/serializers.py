from rest_framework import serializers
from .models import Announcement


class AnnouncementSerializer(serializers.ModelSerializer):
    attachment = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Announcement
        fields = (
            'id', 'title', 'body', 'announcement_type', 'organization_name',
            'reference_number', 'published_date', 'deadline_date', 'attachment', 'is_active'
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, 'published_date') and instance.published_date:
            if hasattr(instance.published_date, 'date'):
                ret['published_date'] = instance.published_date.date()
        if hasattr(instance, 'deadline_date') and instance.deadline_date:
            if hasattr(instance.deadline_date, 'date'):
                ret['deadline_date'] = instance.deadline_date.date()
        if instance.attachment:
            name = instance.attachment.name
            if name.startswith('http://') or name.startswith('https://'):
                ret['attachment'] = name
            else:
                request = self.context.get('request')
                if request:
                    ret['attachment'] = request.build_absolute_uri(
                        instance.attachment.url
                    )
                else:
                    ret['attachment'] = instance.attachment.url
        else:
            ret['attachment'] = None
        return ret
