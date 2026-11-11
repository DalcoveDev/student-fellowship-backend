# ⚙️ Isezerano — Core API & Editorial Backend

> Robust, secure, and production-hardened Django REST API powering the Isezerano digital journalism ecosystem. Features asynchronous background queues, multi-layer in-memory caching, comprehensive editorial workflows, and automated SEO syndication.

---

## 🏛️ High-Level Backend Architecture

```
                                Client / Nginx
                                      │
                                      ▼ (Port 8000)
                     ┌─────────────────────────────────┐
                     │       Gunicorn WSGI Server      │
                     │    (Multi-Worker Concurrency)   │
                     └────────────────┬────────────────┘
                                      │
                                      ▼
                     ┌─────────────────────────────────┐
                     │       Django 6.0 REST Core      │
                     │  (JWT Auth, DRF Serializers,    │
                     │   Sitemaps, Rate Limiting)      │
                     └───────┬─────────────────┬───────┘
                             │                 │
                ┌────────────┴────────┐   ┌────┴────────────┐
                ▼                     ▼   ▼                 ▼
     ┌────────────────────┐   ┌─────────────────┐   ┌─────────────────┐
     │   PostgreSQL 16    │   │  Redis 7 Cache  │   │  Celery Worker  │
     │ Persistent Storage │   │ & Task Broker   │   │ & Beat Dispatch │
     │  (Conn Max Age)    │   │ (< 1ms RAM)     │   │ (Email & Tasks) │
     └────────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## 🧩 Architectural Modules (Apps)

| Application | Core Responsibilities |
|---|---|
| **`articles`** | Article publishing lifecycle, versioned revision history (`ArticleRevision`), category hierarchies, tag taxonomy, and hierarchical comment moderation. |
| **`users`** | Custom User model with granular RBAC permissions (`Reader`, `Journalist`, `Editor`, `Admin`), JWT authentication, and full administrative audit logging (`UserAuditLog`). |
| **`ads`** | Banner slot placement scheduling, native sponsored story engine, impression/click analytics tracking, and automated ad kit inquiry workflows. |
| **`newsletter`** | Subscriber management, HTML email campaign broadcasting, preview test sends, and resilient background email dispatch via Celery & Mailjet. |
| **`layout`** | Dynamic homepage section sequencing, multilingual Daily Verses, recursive multi-level navigation menus, site branding settings, and visitor contact inquiries. |
| **`media_library`**| Digital asset management with strict MIME/extension whitelisting, file size restrictions, and Cloudinary or local storage fallback. |
| **`announcements`**| Community classifieds, official press statements, and public announcements (*Amatangazo*). |

---

## 🌐 Fellowship Website API

The `site_content` app powers the Christian Students Network frontend:

- `GET /api/v1/site-content/` — the site profile and navigation plus ministry expressions, campuses, events, Thursday sessions, gallery, testimonials, leadership teams, teaching articles, and the statement of faith, in the exact shapes the frontend renders.
- `POST /api/v1/inquiries/` — contact, join, and visit form submissions (`kind` = `contact`, `join`, or `visit`), stored in the contact inquiry inbox in the admin.

Seed or refresh the content from the checked-in snapshot with:

```bash
python manage.py seed_site_content
```

The snapshot in `site_content/data/site_content.json` mirrors the frontend's content modules, so the API and the site stay in step.

---

## ⚙️ Settings Architecture

Settings are split for environment isolation and zero development-leakage into production:

```
config/settings/
├── __init__.py    # Dynamic environment router (routes to dev or prod automatically)
├── base.py        # Shared foundation (DRF, JWT, Database, Installed Apps, Sentry, Sitemaps)
├── dev.py         # Local development (DEBUG=True, LocMemCache, permissive origins)
└── prod.py        # Production hardening (DEBUG=False, Redis Cache, HSTS, strict cookies, CSP)
```

---

## ⚡ 5-Layer Caching Strategy

```
Layer 1: Browser Cache ─────────── 30d/365d Cache-Control headers for static assets
Layer 2: Nginx Proxy ───────────── Gzip compression (level 6) & SSL session caching
Layer 3: Next.js Frontend ──────── Server-side component memory caching
Layer 4: Redis In-Memory ───────── < 1ms response caching & throttle counters
Layer 5: PostgreSQL Pool ───────── Persistent connection reuse (CONN_MAX_AGE = 600s)
```

- **Redis Cache**: Configured via `django.core.cache.backends.redis.RedisCache` to absorb high-concurrency reader spikes during breaking news.
- **Connection Pooling**: `CONN_MAX_AGE = 600` keeps database sockets alive across requests, eliminating TCP and TLS handshake overhead.

---

## 🛡️ Security & Hardening Features

- **Obfuscated Administration**: Configurable `ADMIN_URL` path shields the management portal against automated scanners targeting standard `/admin/`.
- **JWT Authentication**: Short-lived 15-minute access tokens with 1-day rotating refresh tokens and blacklist enforcement.
- **Rate Limiting**: Granular throttling applied to authentication (`5/min`), contact inquiries (`3/min`), and anonymous API access (`60/min`).
- **Security Headers**: Strict Transport Security (`HSTS` with preload), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and `Content-Security-Policy`.
- **Least-Privilege Containers**: Production Docker images run under an unprivileged `appuser` system account.

---

## 🔎 SEO & Automated Syndication

- **Article Sitemap (`/sitemap.xml`)**: Dynamic index of all published articles with publication and modification timestamps.
- **Google News Sitemap**: Dedicated feed filtering articles published within the last 48 hours for Google News carousel inclusion.
- **Search Engine Guidance (`/robots.txt`)**: Crawl rules disallowing management portals and internal API endpoints while directing indexers to XML sitemaps.

---

## 📂 Project Directory Structure

```
backend/
├── ads/                    # Advertising slots and analytics tracking
├── announcements/          # Community classifieds & press announcements
├── articles/               # Core article models, serializers, and CMS viewsets
├── config/                 # Project configuration
│   ├── settings/           # Modular settings (base, dev, prod)
│   ├── celery.py           # Celery application initialization
│   ├── email.py            # Mailjet SMTP and API sending engine
│   ├── sitemaps.py         # Google News & article XML sitemaps
│   ├── storage.py          # Resilient Cloudinary / local storage fallback
│   ├── urls.py             # Root URL routing & deep health check endpoint
│   └── wsgi.py             # WSGI deployment entry point
├── deploy/                 # Production deployment orchestration
│   ├── docker-compose.prod.yml # Production multi-container composition
│   └── nginx/              # Nginx reverse proxy configuration
├── layout/                 # Homepage sections, settings, menus, and verses
├── media_library/          # Uploaded image and asset storage
├── newsletter/             # Subscriber lists, campaigns, and Celery tasks
├── users/                  # Custom User model, roles, and audit trails
├── Dockerfile              # Multi-stage production container build
├── entrypoint.sh           # Container startup: migration, static collect, Gunicorn
├── manage.py               # Django management utility
└── requirements.txt        # Direct Python dependencies
```

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- **Python**: `3.12` or `3.13`
- **PostgreSQL**: `16`
- **Redis**: `7`

### Local Setup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create your local `.env` file with your local database connection parameters.

4. Run database migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

6. Open [http://127.0.0.1:8000/api/v1/health/](http://127.0.0.1:8000/api/v1/health/) to verify the API status.

---

## 🧪 Testing & Code Quality

```bash
# Run unit and integration test suite
python manage.py test

# Verify production deployment readiness
python manage.py check --deploy

# Run PEP-8 and code style linter
flake8 .
```

---

## 🐳 Production Deployment (Docker Compose)

The production stack is orchestrated via `deploy/docker-compose.prod.yml` running 7 services:
- **`backend`**: Gunicorn WSGI running Django
- **`frontend`**: Next.js Node.js server
- **`nginx`**: Reverse proxy with SSL termination and Gzip
- **`db`**: PostgreSQL 16 database with persistent storage
- **`redis`**: Redis 7 in-memory cache & task queue
- **`celery`**: Asynchronous worker for emails and background jobs
- **`celery-beat`**: Periodic task scheduler

```bash
cd deploy
docker compose -f docker-compose.prod.yml up -d --build
```

