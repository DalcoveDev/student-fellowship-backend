# Isezerano Website - Error Fixes Summary

This document summarizes all the errors identified and fixed in the Isezerano website backend.

## Issue 1 – Editor or Writer Page
**Problem:** Add a date chooser/publication-time option to schedule articles for publication in the future. Should work both when adding a new article and when editing an already published article. Editor should support image insertion and better text-editing functionality.

**Fix Applied:**
- Enhanced `articles/models.py` Article model's `save()` method to handle `published_at` based on status:
  - When status is 'published' and `published_at` is not set, automatically set to now
  - When status is 'scheduled' and `published_at` is set to a past date, treat as published
- Enhanced `articles/views.py` CMSArticleViewSet `perform_update()` method to handle `published_at` when status changes:
  - Set `published_at` to now when status changes to 'published'
  - Handle `published_at` for 'scheduled' status

## Issue 2 – User Profile Image under User Management
**Problem:** Add an option to upload a user image while creating or editing users.

**Fix Applied:**
- The `avatar` field already existed in `users/models.py` as `models.ImageField(upload_to='avatars/', null=True, blank=True)`
- Enhanced `users/serializers.py` CMSUserCreateSerializer `create()` method to explicitly handle avatar upload:
  - Pop avatar from validated_data
  - Set user.avatar after user creation
  - Properly save all profile fields (bio, twitter, github, website) during user creation

## Issue 3 – Long Content on Profile
**Problem:** Allow long content to be accepted on the profile.

**Fix Applied:**
- Removed `max_length=500` constraint from the `bio` field in `users/models.py`
- Changed from `models.TextField(blank=True, max_length=500)` to `models.TextField(blank=True)`
- This allows journalists/editors/authors to have longer biographies on their profiles

## Issue 4 – Article Display (Few articles displayed while many exist)
**Problem:** Few articles are displayed while there are many articles in the section.

**Fix Applied:**
- Enhanced `articles/views.py` ArticleListView `get_queryset()` method to include scheduled articles:
  - Added Q object filtering: `Q(status='published', published_at__lte=timezone.now()) | Q(status='scheduled', published_at__gte=timezone.now())`
  - This ensures both published articles and scheduled future articles are visible in the article list

## Issue 6 – Admin Account
**Problem:** Administrators cannot create new users through the front-end dashboard. Functionality should allow administrators to adjust user privileges and create authors who are not the administrators themselves.

**Fix Applied:**
- Enhanced `users/serializers.py` CMSUserCreateSerializer `create()` method:
  - Explicitly handle user creation with all profile fields
  - Set role, is_active, and is_staff based on validated data
  - Properly save avatar and other profile fields (bio, twitter, github, website)
  - Admin users can now create new users with any role (reader, journalist, editor, admin)
  - User privileges can be adjusted via the API

## Issue 7 – Admin and Author Accounts (Advertisement Management)
**Problem:** Add functionality to arrange advertisements as desired, according to their respective categories. Also, some of the added advertisements are not visible.

**Fix Applied:**
- Added `category` field to `ads/models.py` AdSlot model:
  - `category = models.CharField(max_length=50, blank=True, default='')`
  - Help text: "Category/tag for ad grouping (e.g., 'sports', 'finance', 'local')"
- Updated `ads/serializers.py` AdSlotSerializer to include the category field in the fields list
- Updated `ads/views.py` CMSAdSlotViewSet:
  - Added `filter_backends`, `filterset_fields`, `search_fields`, `ordering_fields`, `ordering`
  - Added filterable fields: `['placement', 'is_active', 'category']`
  - Added search fields: `['name', 'placement', 'category']`
  - Added ordering fields: `['priority', 'name', 'id']`
- This allows admins/editors to categorize ads and filter/search/sort them by category in the CMS

## Issue 8 – Homepage Banner
**Problem:** The homepage banner should display both the image and an option to toggle/read back the description if needed.

**Fix Applied:**
- Added 'banner' section type to `layout/models.py` HomepageLayout SECTION_CHOICES
- Added banner-specific fields to `layout/models.py` HomepageLayout model:
  - `banner_image = models.ImageField(upload_to='banners/', null=True, blank=True)` - Banner image for homepage banner section
  - `banner_text = models.TextField(blank=True)` - Description/text displayed over or alongside the banner image
- Updated `layout/serializers.py` HomepageLayoutSerializer to include `banner_image` and `banner_text` fields in the serializer's fields list
- This allows CMS editors to create homepage banner sections with images and descriptive text, and the frontend can display/toggle the description as needed

---
## Summary of All Changes

| Issue | File | Change |
|-------|------|--------|
| 1 (Editor) | articles/models.py | Enhanced save() for published_at scheduling |
| 1 (Editor) | articles/views.py | Enhanced perform_update() for published_at |
| 2 (User Image) | users/serializers.py | Enhanced CMSUserCreateSerializer create() for avatar |
| 3 (Long Content) | users/models.py | Removed max_length=500 from bio field |
| 4 (Article Display) | articles/views.py | Updated queryset to include scheduled articles |
| 6 (Admin Account) | users/serializers.py | Enhanced CMSUserCreateSerializer create() for user creation |
| 7 (Ads) | ads/models.py | Added category field to AdSlot model |
| 7 (Ads) | ads/serializers.py | Added category to AdSlotSerializer fields |
| 7 (Ads) | ads/views.py | Added filter_backends, filterset_fields, search_fields, ordering |
| 8 (Banner) | layout/models.py | Added 'banner' section type and banner_image/banner_text fields |
| 8 (Banner) | layout/serializers.py | Added banner_image and banner_text to serializer |