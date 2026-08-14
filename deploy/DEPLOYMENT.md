# Isezerano production deployment

This bundle deploys two sibling GitHub repositories:

```text
/opt/isezerano/
├── isezerano-website-backend/
│   └── deploy/
└── isezerano-website-frontend/
```

Only Nginx exposes host ports (80 and 443). PostgreSQL, Redis, Django,
Celery, and Next.js communicate on private Docker networks.

## 0. Before deployment

1. Rotate the server password that was shared in chat and configure SSH keys.
2. Confirm `prod.isezerano.com` resolves to `161.35.113.160`.
3. Ensure `.env`, uploaded media, virtual environments, `node_modules`, and
   `.next` are not committed.
4. Use a Cloudinary key with `create/upload` permission, or leave all three
   Cloudinary variables blank and rely on the persistent Docker media volume.
5. Use a valid SMTP hostname and provider-specific app password.

## 1. Push the two GitHub repositories

Run these commands on the development machine after replacing the repository
URLs. Review `git status` before each commit.

### Backend

```bash
cd /d/2026-projects/Isezerano/backend
git init
git branch -M main
git remote add origin git@github.com:<ORG>/isezerano-website-backend.git
git add .
git status
git commit -m "Prepare Isezerano backend for production"
git push -u origin main
```

### Frontend

```bash
cd /d/2026-projects/Isezerano/frontend
git init
git branch -M main
git remote add origin git@github.com:<ORG>/isezerano-website-frontend.git
git add .
git status
git commit -m "Prepare Isezerano frontend for production"
git push -u origin main
```

If either directory already has Git metadata or a remote, do not run `git init`
or add a duplicate remote. Inspect with `git remote -v`.

## 2. Prepare Ubuntu 24.04

Log in with the supplied non-root administrator and use `sudo`:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y ca-certificates curl git ufw certbot
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
```

Log out and back in, then verify:

```bash
docker --version
docker compose version
```

Configure the firewall:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

Do not open ports 3000, 5432, 6379, or 8000.

## 3. Give the server read-only GitHub access

For private repositories, create a dedicated SSH deploy key on the server:

```bash
ssh-keygen -t ed25519 -C "isezerano-production-deploy" \
  -f ~/.ssh/isezerano_deploy -N ""
cat ~/.ssh/isezerano_deploy.pub
```

Add the public key as a read-only deploy key to both GitHub repositories. If
GitHub rejects reuse of one deploy key, create one key per repository and use
host aliases in `~/.ssh/config`.

Example for one shared machine-user key:

```sshconfig
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/isezerano_deploy
  IdentitiesOnly yes
```

Test:

```bash
ssh -T git@github.com
```

## 4. Clone the repositories

The directory names matter because Compose uses the frontend sibling path.

```bash
sudo mkdir -p /opt/isezerano
sudo chown "$USER":"$USER" /opt/isezerano
cd /opt/isezerano

git clone git@github.com:<ORG>/isezerano-website-backend.git
git clone git@github.com:<ORG>/isezerano-website-frontend.git
```

## 5. Configure production secrets

```bash
cd /opt/isezerano/isezerano-website-backend/deploy
cp .env.example .env
chmod 600 .env
nano .env
```

Generate safe values:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"  # Django key
openssl rand -base64 36 | tr -d '/+='                         # DB password
openssl rand -base64 36 | tr -d '/+='                         # Redis password
```

Important values:

```env
DEBUG=False
ALLOWED_HOSTS=prod.isezerano.com,161.35.113.160,localhost
CORS_ALLOWED_ORIGINS=https://prod.isezerano.com
CSRF_TRUSTED_ORIGINS=https://prod.isezerano.com
SECURE_SSL_REDIRECT=True
NEXT_PUBLIC_API_URL=https://prod.isezerano.com
```

Do not append `/api` to `NEXT_PUBLIC_API_URL`; frontend code adds `/api/v1`.

Validate interpolation without printing container secrets:

```bash
docker compose --env-file .env -f docker-compose.prod.yml config --services
```

## 6. Build the application

```bash
cd /opt/isezerano/isezerano-website-backend/deploy
mkdir -p certbot/www backups
chmod +x scripts/*.sh

docker compose --env-file .env -f docker-compose.prod.yml build
```

Start everything except Nginx first. Port 80 must remain free while Certbot
performs the initial standalone challenge:

```bash
docker compose --env-file .env -f docker-compose.prod.yml \
  up -d db redis backend celery frontend

docker compose --env-file .env -f docker-compose.prod.yml ps
docker compose --env-file .env -f docker-compose.prod.yml logs --tail=100 backend
```

## 7. Obtain the initial TLS certificate

Confirm DNS before requesting a certificate:

```bash
getent hosts prod.isezerano.com
```

The result must include `161.35.113.160`. Then:

```bash
sudo certbot certonly --standalone \
  --domain prod.isezerano.com \
  --email <OPERATIONS_EMAIL> \
  --agree-tos \
  --no-eff-email
```

Now start Nginx:

```bash
docker compose --env-file .env -f docker-compose.prod.yml up -d nginx
```

Test:

```bash
curl -I https://prod.isezerano.com/
curl -f https://prod.isezerano.com/api/v1/health/
```

## 8. Initialize application data

Migrations and `collectstatic` run automatically in the backend entrypoint.
Create a production administrator:

```bash
docker compose --env-file .env -f docker-compose.prod.yml \
  exec backend python manage.py createsuperuser
```

Only run seed data for a genuinely empty database and change every seeded
password immediately:

```bash
docker compose --env-file .env -f docker-compose.prod.yml \
  exec backend python manage.py seed_data
```

## 9. Smoke tests

Verify all of the following:

- `https://prod.isezerano.com/`
- `https://prod.isezerano.com/api/v1/health/`
- `https://prod.isezerano.com/api/v1/articles/`
- login and `/newsroom`
- create/edit an article and upload a cover
- create/delete an ad
- newsletter subscription confirmation email
- contact/ad-kit email
- `docker compose ... ps` reports healthy containers

Useful logs:

```bash
docker compose --env-file .env -f docker-compose.prod.yml logs -f nginx
docker compose --env-file .env -f docker-compose.prod.yml logs -f backend
docker compose --env-file .env -f docker-compose.prod.yml logs -f celery
```

## 10. Future deployments

Create a backup first:

```bash
cd /opt/isezerano/isezerano-website-backend/deploy
sudo ./scripts/backup.sh
```

Pull and rebuild:

```bash
cd /opt/isezerano/isezerano-website-backend
git pull --ff-only origin main

cd /opt/isezerano/isezerano-website-frontend
git pull --ff-only origin main

cd /opt/isezerano/isezerano-website-backend/deploy
docker compose --env-file .env -f docker-compose.prod.yml build
docker compose --env-file .env -f docker-compose.prod.yml up -d --remove-orphans
docker image prune -f
```

The backend entrypoint applies migrations before Gunicorn starts.

## 11. Certificate renewal

Test renewal:

```bash
sudo /opt/isezerano/isezerano-website-backend/deploy/scripts/renew-certificates.sh
```

Install a root cron entry:

```bash
sudo crontab -e
```

Add:

```cron
17 3 * * * /opt/isezerano/isezerano-website-backend/deploy/scripts/renew-certificates.sh >> /var/log/isezerano-certbot.log 2>&1
```

## 12. Scheduled backups

Test the script:

```bash
sudo /opt/isezerano/isezerano-website-backend/deploy/scripts/backup.sh
```

Then add to root's crontab:

```cron
30 2 * * * BACKUP_DIR=/var/backups/isezerano RETENTION_DAYS=14 /opt/isezerano/isezerano-website-backend/deploy/scripts/backup.sh >> /var/log/isezerano-backup.log 2>&1
```

Copy backups off the Droplet regularly. A backup stored only on the same server
does not protect against server loss.

## 13. Rollback

Record the currently deployed commit before every update:

```bash
git -C /opt/isezerano/isezerano-website-backend rev-parse HEAD
git -C /opt/isezerano/isezerano-website-frontend rev-parse HEAD
```

To roll back application code:

```bash
git -C /opt/isezerano/isezerano-website-backend checkout <BACKEND_COMMIT>
git -C /opt/isezerano/isezerano-website-frontend checkout <FRONTEND_COMMIT>

cd /opt/isezerano/isezerano-website-backend/deploy
docker compose --env-file .env -f docker-compose.prod.yml build
docker compose --env-file .env -f docker-compose.prod.yml up -d
```

Database schema rollbacks require a migration-specific plan. Do not blindly
reverse migrations after production data has been written.
