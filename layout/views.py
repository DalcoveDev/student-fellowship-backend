from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.db import transaction
from .models import HomepageLayout, SiteSetting, DailyVerse, SocialLink, ContactInquiry, MenuItem
from .serializers import (
    HomepageLayoutSerializer, SiteSettingSerializer, DailyVerseSerializer, 
    SocialLinkSerializer, ContactInquirySerializer, MenuItemSerializer, CMSMenuItemSerializer
)
from users.permissions import IsEditor, IsAdmin
from django.utils import timezone

class PublicHomepageLayoutView(generics.ListAPIView):
    serializer_class = HomepageLayoutSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None  # Small dataset; always return plain array

    def get_queryset(self):
        page = self.request.query_params.get('page', 'home')
        return HomepageLayout.objects.filter(is_visible=True, page=page).prefetch_related('categories').order_by('order', 'id')

class PublicSiteSettingView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        setting = SiteSetting.objects.first()
        if not setting:
            # Return default setting parameters if not created yet
            return Response({
                'site_name': 'Isezerano',
                'primary_color': '#2F6DF6',
                'maintenance_mode': False,
                'maintenance_message': 'We are currently performing scheduled system updates and maintenance. We will be back online shortly.',
                'maintenance_contact_email': 'contact@isezerano.com',
                'contact_phone': '+250 788 000 000',
                'contact_email': 'info@isezerano.rw',
                'contact_address': 'Kigali, Rwanda',
                'whatsapp_number': '+250 788 000 000',
                'footer_text': '© 2026 Isezerano. Futuristic Digital Journalism.'
            })
        serializer = SiteSettingSerializer(setting)
        return Response(serializer.data)

class PublicMenuView(generics.ListAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None

    def get_queryset(self):
        position = self.request.query_params.get('position', 'header_main')
        # Only return top-level items (parent=None); children will be recursively serialized
        return MenuItem.objects.filter(
            is_visible=True, 
            position=position, 
            parent=None
        ).prefetch_related('children', 'children__children', 'category').order_by('order', 'id')

class ContactInquiryCreateView(generics.CreateAPIView):
    serializer_class = ContactInquirySerializer
    permission_classes = (permissions.AllowAny,)

class CMSContactInquiryViewSet(viewsets.ModelViewSet):
    queryset = ContactInquiry.objects.all().order_by('-created_at')
    serializer_class = ContactInquirySerializer
    permission_classes = (IsEditor,)

# ================= CMS API VIEWS =================

class CMSHomepageLayoutViewSet(viewsets.ModelViewSet):
    serializer_class = HomepageLayoutSerializer
    permission_classes = (IsEditor,)
    pagination_class = None

    def get_queryset(self):
        queryset = HomepageLayout.objects.all().prefetch_related('categories')
        page = self.request.query_params.get('page')
        if page:
            queryset = queryset.filter(page=page)
        return queryset.order_by('order', 'id')

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Batch reorder sections in a single atomic transaction."""
        items = request.data.get('items', [])
        with transaction.atomic():
            for item in items:
                item_id = item.get('id')
                if item_id:
                    update_data = {}
                    if 'order' in item:
                        update_data['order'] = item['order']
                    if 'is_visible' in item:
                        update_data['is_visible'] = item['is_visible']
                    if 'article_limit' in item:
                        update_data['article_limit'] = item['article_limit']
                    if update_data:
                        HomepageLayout.objects.filter(id=item_id).update(**update_data)
        return Response({'status': 'success', 'message': 'Sections reordered successfully'})

class CMSMenuItemViewSet(viewsets.ModelViewSet):
    serializer_class = CMSMenuItemSerializer
    permission_classes = (IsEditor,)
    pagination_class = None

    def get_queryset(self):
        position = self.request.query_params.get('position')
        queryset = MenuItem.objects.all().prefetch_related('category', 'parent')
        if position:
            queryset = queryset.filter(position=position)
        return queryset.order_by('order', 'id')

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Batch reorder menus and update parent hierarchy in a single atomic transaction."""
        items = request.data.get('items', [])
        with transaction.atomic():
            for item in items:
                item_id = item.get('id')
                if item_id:
                    update_data = {}
                    if 'order' in item:
                        update_data['order'] = item['order']
                    if 'parent' in item:
                        update_data['parent_id'] = item['parent']
                    if 'is_visible' in item:
                        update_data['is_visible'] = item['is_visible']
                    if update_data:
                        MenuItem.objects.filter(id=item_id).update(**update_data)
        return Response({'status': 'success', 'message': 'Menus reordered successfully'})

class CMSSiteSettingViewSet(viewsets.ModelViewSet):
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    permission_classes = (IsEditor,)
    pagination_class = None

    def get_object(self):
        # Always operate on the singleton instance
        obj, created = SiteSetting.objects.get_or_create(id=1)
        return obj

class DailyVerseTodayView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        today = timezone.localdate()
        verse = DailyVerse.objects.filter(date=today).first()
        if not verse:
            # Fallback to the latest verse if none for today
            verse = DailyVerse.objects.order_by('-date').first()
            
        if not verse:
            return Response({
                'verse_reference': 'Habakuki 2:3',
                'verse_text_kinyarwanda': 'Kuko ibyo kwerekwa bifite igihe byabariwe...',
                'verse_text_english': 'For the revelation awaits an appointed time...',
                'verse_text_french': 'Car la vision est encore pour un temps fixé...',
            })
        serializer = DailyVerseSerializer(verse)
        return Response(serializer.data)

class CMSDailyVerseViewSet(viewsets.ModelViewSet):
    queryset = DailyVerse.objects.all()
    serializer_class = DailyVerseSerializer
    permission_classes = (IsEditor,)
    pagination_class = None

class CMSSocialLinkViewSet(viewsets.ModelViewSet):
    queryset = SocialLink.objects.all()
    serializer_class = SocialLinkSerializer
    permission_classes = (IsEditor,)
    pagination_class = None

class PublicSocialLinkListView(generics.ListAPIView):
    queryset = SocialLink.objects.all().order_by('order')
    serializer_class = SocialLinkSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None  # Small dataset; always return plain array


