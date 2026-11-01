# Isezerano Website — Issue Verification & Fix Report

**Date:** 2026-11-01  
**Backend:** `D:\ISEZERANO -WEB-SITE\isezerano-website-backend`  
**Frontend:** `D:\ISEZERANO -WEB-SITE\isezerano-website-frontend`  
**Environment:** Django + PostgreSQL, Next.js, local development servers at `http://127.0.0.1:8000` and `http://localhost:3000`.

All seven reported issues were reproduced/confirmed in the code and API, fixed, and verified. Existing uncommitted work in both repositories was preserved.

## Summary

| # | Issue | Status | Result |
|---|-------|--------|--------|
| 1 | Schedule new/existing articles; improve editor with images and text editing | ✅ Fixed | Future publication dates are saved as `scheduled`, due articles publish automatically, CMS has schedule presets/status, and the editor gained undo/redo, keyboard shortcuts, image URL insertion, drag/drop and paste uploads. |
| 2 | Upload profile image while creating/editing users | ✅ Fixed | Create and edit user forms support avatar preview, upload, and removal; the backend now persists avatars on account creation. |
| 3 | Allow long profile content | ✅ Fixed | Removed the 500-character model limit; the CMS textarea and public author card handle multi-thousand-character biographies. |
| 4 | Show more articles in sections when many exist | ✅ Fixed | Public API supports `?limit=` up to 200, the frontend paginates until it has enough articles, and homepage/category/dynamic pages request up to 200. Section limit editing now saves the live value. |
| 5 | Admins create users, adjust privileges, and create non-admin authors | ✅ Fixed | Superusers are synced to `admin`/`is_staff`, role changes work for non-superuser admins, and self-lockout is prevented. |
| 6 | Arrange ads by category; make all added ads visible | ✅ Fixed | Ads have a category, the public endpoint can return all active ads for a placement, `AdSpace` rotates them, and the manager supports category filtering/grouping plus description toggles. |
| 7 | Homepage banner image plus toggle/read-back description | ✅ Fixed | New `banner` section supports image upload, description, default visibility toggle, and visitor show/hide; the public page renders all of it. |

---

## 1. Article scheduling and rich editor

### Confirmed problem
The CMS already had `scheduled` in its status model, but scheduling was not reliable: publication dates and statuses could disagree, due articles were not promoted without Celery, and the public API had no clean rule for scheduled content. The editor also lacked common writing conveniences and image insertion beyond a plain upload.

### Fixes

**Backend**
- Added `Article.publish_due_scheduled()` to promote `scheduled` articles whose `published_at` has passed.
- Updated `Article.save()` to keep status/publication date consistent:
  - `published` without a date gets the current time.
  - `published` with a future date becomes `scheduled`.
  - `scheduled` with a due date becomes `published`.
  - `update_fields` is corrected when `save()` changes status.
- Public list and detail views promote due articles on read, so scheduling works without Celery running.
- Public article queries now expose only published articles with a due or empty publication date.
- Added serializer validation that rejects missing or past schedules for new/transitioned scheduled articles.
- Configured Celery beat (`publish-scheduled-articles-every-minute`) for deployments that run Celery.
- Added the `change_author` CMS action and `full_name` in author options.

**Frontend**
- Create/edit article pages: `scheduled` status option, future-date validation, schedule presets (`+1 Hour`, `Tomorrow 9:00`, `In a Week`), and status-aware submit labels.
- CMS article list: scheduled tab, scheduled badge/date, and **Publish Now** action.
- `RichArticleEditor.tsx`:
  - Undo/redo with buttons and `Ctrl+Z` / `Ctrl+Shift+Z` / `Ctrl+Y`.
  - `Ctrl+B`, `Ctrl+I`, `Ctrl+K` shortcuts.
  - Clear formatting.
  - Insert image from URL dialog.
  - Drag/drop and clipboard paste image uploads.
  - Larger image/video controls and safer HTML escaping.

### Verification
- `manage.py check` → `System check identified no issues (0 silenced).`
- `manage.py test articles users ads layout --keepdb` → **44 tests passed**.
- Scheduling API script:

```text
create: 201
stored status: scheduled
stored published_at future: True
public list before due contains it: False
public detail before due status: 404
public list after due contains it: True
public detail after due status: 200
status after due read: published
past-schedule create rejected: True
```

- Browser check of `/newsroom/articles/create`: status select contains `scheduled`, presets render, and editor tools **Undo, Redo, Bold, Insert Link, Direct Upload Image** are present.

### Key files
- Backend: `articles/models.py`, `articles/serializers.py`, `articles/views.py`, `config/celery.py`
- Frontend: `src/app/newsroom/articles/create/page.tsx`, `src/app/newsroom/articles/[id]/edit/page.tsx`, `src/app/newsroom/articles/page.tsx`, `src/components/RichArticleEditor.tsx`

---

## 2. Profile image upload for users

### Confirmed problem
The user model had an `avatar` field, but the CMS create flow did not reliably persist an uploaded avatar, and the user management UI had no upload/preview controls.

### Fixes
- `CMSUserCreateSerializer.create()` now saves the uploaded avatar and copies all profile fields (`bio`, `twitter`, `github`, `website`) during account creation.
- User management page now supports:
  - Avatar preview while creating and editing.
  - File selection with image-type and 5 MB validation.
  - Removal of an existing avatar.
  - `FormData` submissions for create/update.
  - Avatar thumbnails in the user directory and error display.

### Verification
```text
create status: 201
create has avatar: True
stored avatar name: avatars/create-avatar.png
role journalist is_staff: True
update status: 200
update has avatar: True
stored updated avatar: avatars/updated-avatar.png
```

Browser check of the **Create Operator Account** modal confirmed the profile-image upload control is present.

### Key files
- Backend: `users/serializers.py`
- Frontend: `src/app/newsroom/users/page.tsx`

---

## 3. Long profile content

### Confirmed problem
`User.bio` was a `TextField` but still had `max_length=500`, so longer biographies were rejected or truncated. The CMS textarea was also small.

### Fixes
- Removed the 500-character limit from `User.bio`; migration `users/migrations/0003_alter_user_bio.py` applies the change.
- User form biography textarea increased to 5 rows, resizable, with a live character counter and a hint that long biographies are supported.
- Public author card now:
  - Uses the uploaded avatar.
  - Shows the full biography with `whitespace-pre-line break-words`.
  - Uses `flex-1 min-w-0` so long content does not break the layout.

### Verification
```text
create status: 201
submitted bio length: 6819
stored bio length: 6819
stored matches: True
update status: 200
updated bio length: 6847
updated matches: True
```

The browser check confirmed the biography textarea accepts long content (5-row resizable field with character counter).

### Key files
- Backend: `users/models.py`, `users/migrations/0003_alter_user_bio.py`
- Frontend: `src/app/newsroom/users/page.tsx`, public author components

---

## 4. More articles in sections

### Confirmed problem
The public article endpoint returned a fixed page (50 items), and sections requested only their display limit. As article volume grew, later articles were not available to homepage/category sections even when a section was configured to show more.

### Fixes
- Added `ArticlePagination`:
  - Default page size: 50.
  - `?limit=` query parameter.
  - Maximum page size: 200.
- Attached the paginator to `ArticleListView`.
- Frontend `useArticles(limit)` now keeps requesting pages until it collects `limit` articles or the feed is exhausted.
- Homepage requests up to 200 articles.
- Category and dynamic page views request `?limit=200`.
- Section manager limit input now reads the live input value and persists it (previously it could save stale state).

### Verification
- API check:

```text
limit=5 returned: 5 total: 100
limit=200 returned: 100 total: 100
```

- Browser check of homepage: **35 unique article links** rendered.
- Browser check of `/c/business`: **20 unique article links** rendered.

### Key files
- Backend: `articles/views.py`
- Frontend: `src/lib/useArticles.ts`, `src/app/(public)/page.tsx`, `src/app/(public)/c/[slug]/page.tsx`, `src/app/(public)/[slug]/page.tsx`, `src/app/newsroom/sections/page.tsx`

---

## 5. Admin user management and privileges

### Confirmed problem
Superuser accounts could still have role `reader`, so the frontend redirected them away from the CMS even though Django considered them superusers. There was also no protection against an admin changing their own role or deactivating themselves.

### Fixes
- `User.save()` now forces superusers to:
  - `role = 'admin'`
  - `is_staff = True`
  - Correct `update_fields` handling.
- Added data migration `users/migrations/0004_sync_superuser_role.py` and applied it.
- Current superuser state:
  - `ingabiredalcove` → `admin`, `is_staff=True`, active.
  - `dalcoveadmin` → `admin`, `is_staff=True`, inactive.
- Added `CMSUserSerializer.validate()` self-protection:
  - Cannot change own role.
  - Cannot deactivate own account.
- User create/edit modals explain role privileges (reader, journalist, editor, admin).

### Verification
```text
admin role: admin superuser: False
create author status: 201
created role: journalist is_staff: True superuser: False
promote to editor status: 200
role after promote: editor is_staff: True
create admin status: 201
created admin role: admin is_staff: True
reader access status: 403
```

### Key files
- Backend: `users/models.py`, `users/serializers.py`, `users/migrations/0004_sync_superuser_role.py`
- Frontend: `src/app/newsroom/users/page.tsx`

---

## 6. Ad categories and invisible ads

### Confirmed problem
- Every ad belonged to a placement but had no category, so the manager could not group or target campaigns by section.
- The public ad endpoint returned only the single highest-priority active ad. Newly added lower-priority ads existed in the database but never appeared on the site.
- Category pages had no category-specific ad placements.

### Fixes

**Backend**
- Added `AdSlot.category` (free-form grouping/targeting field).
- Added `AdSlot.show_description` and a CMS `toggle-description` action.
- Added category placements:
  - `category_bottom_banner`
  - `category_sidebar_2`
  - `category_sidebar_3`
- `ActiveAdView` now:
  - Accepts `?category=`.
  - Prefers category-specific plus generic ads.
  - Falls back to any active ad in that placement.
  - Accepts `?all=true` to return every active ad for rotation.
- CMS ad list orders/filters by category and priority.

**Frontend**
- Ads manager:
  - Category field on create/edit.
  - Category filter and table column.
  - Category arrangement selector.
  - Expanded placement options.
- `AdSpace.tsx`:
  - Requests all active ads for the placement.
  - Rotates campaigns every 15 seconds.
  - Resets impression tracking per ad.
  - Passes the current category from category and article pages.
- Category page and in-article ads now send the category slug.

### Verification
```text
create Sports verification ad: 201 (category: sports)
create Finance verification ad: 201 (category: finance)
create Global verification ad: 201 (category: "")
all ads status: 200 count: 3
all ad names: ['Sports verification ad', 'Finance verification ad', 'Global verification ad']
sports-targeted names: ['Sports verification ad', 'Global verification ad']
sports ad is first: True
finance single status: 200
finance single name: Finance verification ad
toggle status: 200 value: False
cms grouped categories: ['', '', 'finance', 'sports']
```

Browser check of `/newsroom/ads` confirmed the **Category** column and **Arrange by Category** selector render. Empty ad placements log expected `404` responses when no campaign exists; they do not cause JavaScript errors.

### Key files
- Backend: `ads/models.py`, `ads/serializers.py`, `ads/views.py`, `ads/migrations/0005_adslot_category.py`, `ads/migrations/0006_adslot_show_description_alter_adslot_placement.py`
- Frontend: `src/components/AdSpace.tsx`, `src/app/newsroom/ads/page.tsx`, `src/app/(public)/c/[slug]/page.tsx`, `src/app/(public)/a/[slug]/page.tsx`

---

## 7. Homepage banner image and description toggle

### Confirmed problem
The layout model had banner image/text support, but:
- There was no `banner` section type in the editor workflow.
- The description visibility was not persisted.
- The public pages did not render a banner section with image + description.
- There was no visitor control to hide/show the description.

### Fixes

**Backend**
- Added `banner_show_description` to `HomepageLayout` (default `True`).
- Exposed `banner_image`, `banner_text`, and `banner_show_description` in `HomepageLayoutSerializer`.
- Migration `layout/migrations/0010_homepagelayout_banner_show_description.py` applied.
- CMS layout endpoint accepts multipart banner-image uploads.

**Frontend**
- Added **Homepage / Page Banner (Image + Description)** to the section type dropdown.
- Banner editor supports:
  - Image upload with preview and 5 MB validation.
  - Description textarea with character count.
  - **Show description by default** checkbox.
- Edit modal loads existing image, description, and toggle state.
- Duplicate and create flows carry banner text/toggle; image is uploaded after create/edit.
- Section card shows a thumbnail and banner status details.
- New reusable `BannerSection.tsx` renders:
  - The uploaded image.
  - The description when enabled.
  - A **Hide description / Show description** toggle initialized from `banner_show_description`.
- Wired into homepage `src/app/(public)/page.tsx` and dynamic `src/app/(public)/[slug]/page.tsx`.

### Verification
Backend API:
```text
create banner section: 201
initial banner_show_description: False
initial banner_text: This is the banner description shown to readers.
upload banner image: 200
public layout status: 200
public block found: True
public banner_image present: True
public banner_text: This is the banner description shown to readers.
public banner_show_description: False
toggle description on: 200 True
public read-back after toggle: True
```

CMS UI:
- Edit modal loaded `banner_text`, the uploaded preview, and the checked toggle.
- Saving through the UI persisted:
  - `text: UI SAVE VERIFICATION: description updated from the section editor.`
  - `image: banners/sections-create-banner.png`
- Create modal rendered the upload control, description field, and default-visibility checkbox.

Public UI:
- Banner image, description, and toggle rendered on the homepage.
- Clicking the toggle changed the label `Hisha ibisobanuro` → `Erekana ibisobanuro`, hid the description, and restored it on the second click.
- Temporary verification banner data was removed after testing; no production content was left behind.

### Key files
- Backend: `layout/models.py`, `layout/serializers.py`, `layout/migrations/0009_homepagelayout_banner_image_and_more.py`, `layout/migrations/0010_homepagelayout_banner_show_description.py`
- Frontend: `src/app/newsroom/sections/page.tsx`, `src/components/BannerSection.tsx`, `src/app/(public)/page.tsx`, `src/app/(public)/[slug]/page.tsx`

---

## Global verification

| Check | Result |
|-------|--------|
| `python manage.py check` | No issues |
| `python manage.py test articles users ads layout --keepdb` | 44 tests passed |
| `npx tsc --noEmit` | No TypeScript errors |
| `npx eslint` on changed frontend files | 0 errors; only existing/unused-symbol warnings |
| Scheduling API flow | Passed |
| Media upload API | `201`, file URL returned |
| Avatar create/update API | `201` / `200` with stored files |
| 6,819-character bio create + 6,847-character PATCH | Passed |
| Admin creates journalist/editor/admin; reader denied | Passed (201/200/201/403) |
| Ad category targeting, `?all=true`, description toggle | Passed |
| Banner upload, public read-back, toggle persistence | Passed |
| Public homepage/category/article pages | Rendered with article content |
| CMS ads/users/articles/sections pages | Rendered and usable |

## Migrations to apply on deployment

```text
users/migrations/0003_alter_user_bio.py
users/migrations/0004_sync_superuser_role.py
ads/migrations/0005_adslot_category.py
ads/migrations/0006_adslot_show_description_alter_adslot_placement.py
layout/migrations/0009_homepagelayout_banner_image_and_more.py
layout/migrations/0010_homepagelayout_banner_show_description.py
```

Run:

```bash
python manage.py migrate
```

## Deployment notes

1. Ensure media storage is writable for `avatars/`, `ads/`, `banners/`, and article/media uploads.
2. Rebuild the frontend after pulling these changes (`npm run build`).
3. Celery beat is configured for scheduled publishing, but is not required: public article reads promote due scheduled articles automatically.
4. Empty ad placements return `404` by design (`No active ads found`); this is not a frontend crash and does not block page rendering.

## Repository hygiene

- All changes remain uncommitted in both repositories.
- Unrelated pre-existing modified files (for example deployment config, Django settings, frontend package/build metadata) were left untouched.
- Temporary verification data (test users, test ads, test banner section, uploaded verification images) was removed after verification.
