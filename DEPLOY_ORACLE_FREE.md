# Oracle Cloud Always Free Deployment

This is the best zero-cost production path for this project as it exists today:

- one Oracle Cloud Always Free Ubuntu VM
- PostgreSQL on the same VM
- FastAPI backend as a `systemd` service
- React frontend built to static files and served by Nginx
- one public IP or one domain for the whole app

Why this option:

- no sleep/spin-down like Render free web services
- no 30-day database expiry like Render free Postgres
- no multi-service free-tier juggling
- enough RAM and CPU for a small internal school office portal

## Recommended architecture

- `Nginx` serves the frontend from `/var/www/school-fee-portal`
- `Nginx` proxies `/api` and `/health` to `127.0.0.1:8000`
- `uvicorn` runs the backend only on localhost
- `PostgreSQL` runs locally on port `5432`

## 1. Create the Oracle VM

Recommended:

- Ubuntu 24.04
- `VM.Standard.A1.Flex`
- `2 OCPU`
- `12 GB RAM`
- `100 GB` boot volume

That is already more than enough for this app. You can scale within the Always Free limits later if needed.

Open these ports in the Oracle security list and in `ufw`:

- `22` for SSH
- `80` for HTTP
- `443` for HTTPS if you later add a domain and Certbot

## 2. Install system packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip postgresql postgresql-contrib nginx nodejs npm rsync
```

If your Node version is too old, install a newer LTS release before building the frontend.

## 3. Clone the project

```bash
cd /opt
sudo git clone https://github.com/rohithreddy999/SchoolPortal_Chaos.git school-fee-portal
sudo chown -R $USER:$USER /opt/school-fee-portal
cd /opt/school-fee-portal
git checkout dev/kalyan
```

## 4. Create the PostgreSQL database

```bash
sudo -u postgres psql
```

Inside `psql`:

```sql
CREATE USER school_portal WITH PASSWORD 'change-me';
CREATE DATABASE school_portal OWNER school_portal;
\q
```

## 5. Configure backend environment

```bash
cp backend/.env.production.example backend/.env
nano backend/.env
```

Set at least:

- a strong `SECRET_KEY`
- a strong `DEFAULT_ADMIN_PASSWORD`
- the real database password
- your domain or public IP in `BACKEND_CORS_ORIGINS`

## 6. Install backend and run migrations

```bash
cd /opt/school-fee-portal/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
```

## 7. Build the frontend

```bash
cd /opt/school-fee-portal/frontend
cp .env.production.example .env.production
npm ci
npm run build
sudo mkdir -p /var/www/school-fee-portal
sudo rsync -a --delete dist/ /var/www/school-fee-portal/
```

The frontend is prepared to use `/api`, so frontend and backend can live behind the same domain.

## 8. Install the backend service

```bash
sudo cp /opt/school-fee-portal/deploy/oracle/school-portal-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable school-portal-backend
sudo systemctl start school-portal-backend
sudo systemctl status school-portal-backend
```

## 9. Install the Nginx site

```bash
sudo cp /opt/school-fee-portal/deploy/oracle/nginx-school-portal.conf /etc/nginx/sites-available/school-fee-portal
sudo ln -sf /etc/nginx/sites-available/school-fee-portal /etc/nginx/sites-enabled/school-fee-portal
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

Now the app should open on:

- `http://YOUR_SERVER_IP`

## 10. Optional: add HTTPS

If you point a real domain to the VM:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.example
```

Then update `BACKEND_CORS_ORIGINS` to include the final HTTPS domain.

## Updates after deployment

Use the helper script:

```bash
cd /opt/school-fee-portal
chmod +x deploy/oracle/redeploy.sh
./deploy/oracle/redeploy.sh
```

It will:

- pull latest code
- install backend packages
- apply migrations
- build the frontend
- sync frontend files into Nginx web root
- restart backend
- reload Nginx

## Operations advice

- run `backup.ps1` on your main machine or create a Linux `pg_dump` cron job on the server
- change the default admin password immediately after first login
- keep the VM private except for `80/443/22`
- if you store real Aadhaar data, use a strong password and strong VM access controls

## If you want the easiest path instead of the best free path

Use:

- Cloudflare Pages for frontend
- Render for backend
- Neon for PostgreSQL

That is easier, but it is weaker for a real school production system than one Always Free VM.
