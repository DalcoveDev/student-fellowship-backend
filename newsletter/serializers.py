from rest_framework import serializers
from .models import Subscriber, NewsletterCampaign

class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = ('id', 'email', 'is_active', 'subscribed_at')
        read_only_fields = ('id', 'subscribed_at')

class NewsletterCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterCampaign
        fields = ('id', 'subject', 'body', 'status', 'sent_at', 'created_at')
        read_only_fields = ('id', 'status', 'sent_at', 'created_at')
