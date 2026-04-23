#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/opt/school-fee-portal"
BACKEND_DIR="$APP_ROOT/backend"
FRONTEND_DIR="$APP_ROOT/frontend"
WEB_ROOT="/var/www/school-fee-portal"

cd "$APP_ROOT"
git pull

cd "$BACKEND_DIR"
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head

cd "$FRONTEND_DIR"
npm ci
npm run build

sudo mkdir -p "$WEB_ROOT"
sudo rsync -a --delete dist/ "$WEB_ROOT/"

sudo systemctl restart school-portal-backend
sudo systemctl reload nginx

echo "Deployment finished."
