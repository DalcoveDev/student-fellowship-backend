from rest_framework import serializers

from .models import (
    Campus,
    FaithSection,
    GalleryImage,
    LeadershipTeam,
    MinistryExpression,
    SiteArticle,
    SiteEvent,
    SiteProfile,
    Testimonial,
    ThursdaySession,
)


class SiteProfileSerializer(serializers.ModelSerializer):
    shortName = serializers.CharField(source='short_name')
    joinPhone = serializers.JSONField(source='join_phone')
    url = serializers.CharField(source='site_url')

    class Meta:
        model = SiteProfile
        fields = (
            'name', 'shortName', 'tagline', 'mission', 'vision', 'email',
            'phones', 'joinPhone', 'location', 'url', 'socials',
        )


class MinistryExpressionSerializer(serializers.ModelSerializer):
    imageAlt = serializers.CharField(source='image_alt')

    class Meta:
        model = MinistryExpression
        fields = ('number', 'title', 'description', 'href', 'image', 'imageAlt')


class CampusSerializer(serializers.ModelSerializer):
    shortName = serializers.CharField(source='short_name')
    type = serializers.CharField(source='campus_type')
    imageAlt = serializers.CharField(source='image_alt')

    class Meta:
        model = Campus
        fields = (
            'slug', 'name', 'shortName', 'type', 'description', 'detail',
            'image', 'imageAlt',
        )


class SiteEventSerializer(serializers.ModelSerializer):
    dateLabel = serializers.CharField(source='date_label')
    imageAlt = serializers.CharField(source='image_alt')

    class Meta:
        model = SiteEvent
        fields = (
            'day', 'month', 'dateLabel', 'title', 'kind', 'description',
            'image', 'imageAlt',
        )


class ThursdaySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThursdaySession
        fields = ('session', 'time')


class GalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryImage
        fields = ('src', 'alt', 'title', 'category')


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ('quote', 'name', 'role')


class LeadershipTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadershipTeam
        fields = ('slug', 'title', 'summary', 'responsibilities')


class FaithSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaithSection
        fields = ('slug', 'title', 'paragraphs', 'scripture')


class SiteArticleSerializer(serializers.ModelSerializer):
    imageAlt = serializers.CharField(source='image_alt')

    class Meta:
        model = SiteArticle
        fields = (
            'slug', 'title', 'category', 'excerpt', 'image', 'imageAlt',
            'sections', 'scripture',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # The frontend omits ``scripture`` when an article has no pull quote.
        if not data.get('scripture'):
            data.pop('scripture', None)
        return data
