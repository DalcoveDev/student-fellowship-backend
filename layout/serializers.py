from rest_framework import serializers
from .models import HomepageLayout, SiteSetting, DailyVerse, SocialLink, ContactInquiry, MenuItem
from articles.serializers import CategorySerializer
from articles.models import Category
from ads.serializers import AdSlotSerializer
from ads.models import AdSlot


class HomepageLayoutSerializer(serializers.ModelSerializer):
    category_details = CategorySerializer(source='category', read_only=True)
    categories_details = CategorySerializer(source='categories', many=True, read_only=True)
    ad_slot_details = AdSlotSerializer(source='ad_slot', read_only=True)

    categories = serializers.PrimaryKeyRelatedField(many=True, queryset=Category.objects.all(), required=False)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    ad_slot = serializers.PrimaryKeyRelatedField(queryset=AdSlot.objects.all(), required=False, allow_null=True)
    article_limit = serializers.IntegerField(required=False, allow_null=True, default=5)

    class Meta:
        model = HomepageLayout
        fields = (
            'id', 'page', 'section_type', 'order', 'category', 'categories', 'ad_slot',
            'is_visible', 'article_limit', 'title', 'content', 'video_url', 'display_variant',
            'category_details', 'categories_details', 'ad_slot_details',
            'banner_image', 'banner_text', 'banner_show_description'
        )


class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = (
            'site_name', 'logo_light', 'logo_dark',
            'primary_color', 'secondary_color', 'font_color', 'bg_color',
            'btn_bg_color', 'btn_text_color', 'link_color', 'hover_color',
            'font_family_body', 'font_family_headings', 'active_theme', 'custom_css',
            'maintenance_mode', 'maintenance_message', 'maintenance_contact_email',
            'contact_phone', 'contact_email', 'contact_address', 'whatsapp_number',
            'facebook_url', 'twitter_url', 'instagram_url', 'youtube_url', 'linkedin_url', 'tiktok_url',
            'footer_text', 'footer_recent_limit', 'homepage_limit'
        )


class MenuItemSerializer(serializers.ModelSerializer):
    category_details = CategorySerializer(source='category', read_only=True)
    target_url = serializers.CharField(read_only=True)
    depth = serializers.IntegerField(source='get_depth', read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = (
            'id', 'title', 'title_rw', 'title_fr', 'parent', 'menu_type',
            'page_slug', 'category', 'category_details', 'article_slug',
            'custom_url', 'target_url', 'position', 'order', 'is_visible',
            'open_in_new_tab', 'icon_name', 'depth', 'children'
        )

    def get_children(self, obj):
        # Recursively serialize visible children in order
        children = obj.children.filter(is_visible=True).order_by('order', 'id')
        return MenuItemSerializer(children, many=True, context=self.context).data


class CMSMenuItemSerializer(serializers.ModelSerializer):
    category_details = CategorySerializer(source='category', read_only=True)
    target_url = serializers.CharField(read_only=True)
    depth = serializers.IntegerField(source='get_depth', read_only=True)

    class Meta:
        model = MenuItem
        fields = (
            'id', 'title', 'title_rw', 'title_fr', 'parent', 'menu_type',
            'page_slug', 'category', 'category_details', 'article_slug',
            'custom_url', 'target_url', 'position', 'order', 'is_visible',
            'open_in_new_tab', 'icon_name', 'depth'
        )


class ContactInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInquiry
        fields = (
            'id', 'kind', 'name', 'email', 'phone', 'contact', 'campus',
            'session', 'subject', 'message', 'created_at', 'is_read',
        )
        read_only_fields = ('id', 'created_at')


class SiteInquirySerializer(serializers.ModelSerializer):
    """Validation for the website's contact, join, and visit forms."""

    email = serializers.EmailField(required=False, allow_blank=True)
    contact = serializers.CharField(required=False, allow_blank=True, max_length=200)
    campus = serializers.CharField(required=False, allow_blank=True, max_length=200)
    session = serializers.CharField(required=False, allow_blank=True, max_length=200)
    subject = serializers.CharField(required=False, allow_blank=True, max_length=200)
    message = serializers.CharField(required=False, allow_blank=True, max_length=5000)

    class Meta:
        model = ContactInquiry
        fields = (
            'id', 'kind', 'name', 'email', 'contact', 'campus', 'session',
            'subject', 'message', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def validate(self, attrs):
        kind = attrs.get('kind', 'contact')
        errors = {}

        if not attrs.get('name', '').strip():
            errors['name'] = 'Please enter your name.'

        if kind == 'contact':
            if not attrs.get('email', '').strip():
                errors['email'] = 'Please enter your email address.'
            if not attrs.get('subject', '').strip():
                errors['subject'] = 'Please choose a subject.'
            if not attrs.get('message', '').strip():
                errors['message'] = 'Please write a message.'
        else:
            if not attrs.get('contact', '').strip() and not attrs.get('email', '').strip():
                errors['contact'] = 'Please leave a phone number or email address.'
            if not attrs.get('subject', '').strip():
                attrs['subject'] = (
                    'Bible study enquiry' if kind == 'join' else 'Visit plan'
                )

        if errors:
            raise serializers.ValidationError(errors)

        for field in ('name', 'email', 'contact', 'campus', 'session', 'subject', 'message'):
            value = attrs.get(field)
            if isinstance(value, str):
                attrs[field] = value.strip()

        return attrs


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ('id', 'platform', 'custom_name', 'url', 'icon_name', 'order')


class DailyVerseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyVerse
        fields = ('id', 'date', 'verse_reference', 'verse_text_kinyarwanda', 'verse_text_english', 'verse_text_french')
