from rest_framework import serializers
from .models import AdSlot, AnalyticsEvent

class AdSlotSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    sponsored_logo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = AdSlot
        fields = (
            'id', 'name', 'placement', 'image', 'html_content', 'target_url', 
            'cta_text', 'sponsored_logo', 'sponsored_headline', 'sponsored_video_url',
            'start_date', 'end_date', 'priority', 'impressions', 'clicks', 'is_active', 'ctr'
        )
        read_only_fields = ('id', 'impressions', 'clicks', 'ctr')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        for field in ('image', 'sponsored_logo'):
            file_field = getattr(instance, field)
            if file_field:
                name = file_field.name
                if name.startswith('http://') or name.startswith('https://'):
                    ret[field] = name
                elif request:
                    ret[field] = request.build_absolute_uri(file_field.url)
                else:
                    ret[field] = file_field.url
        return ret

class AnalyticsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsEvent
        fields = ('id', 'event_type', 'article', 'ad_slot', 'ip_address', 'user_agent', 'referrer', 'created_at')
        read_only_fields = ('id', 'created_at')
