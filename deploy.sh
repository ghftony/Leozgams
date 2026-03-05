#!/bin/bash
# Deployment script for gohifun (Parkour Game)
#
# == HOW TO DEPLOY ==
# 1. SSH into the VPS
# 2. Pull latest code and run deploy steps:
#      cd /home/gohifun
#      git pull origin claude/import-parkour-game-uOA3I
#      source venv/bin/activate
#      python manage.py migrate
#      bash deploy.sh
# ==================

set -e

echo "==> Activating virtual environment..."
source venv/bin/activate

echo "==> Running migrations..."
python manage.py migrate

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Restarting gunicorn service..."
sudo systemctl restart gohifun

echo "==> Purging Cloudflare cache for /static/*..."
# Requires CF_ZONE_ID and CF_API_TOKEN environment variables to be set.
# Set them in /etc/environment or your server's systemd drop-in.
if [ -z "$CF_ZONE_ID" ] || [ -z "$CF_API_TOKEN" ]; then
  echo "    WARNING: CF_ZONE_ID or CF_API_TOKEN not set — skipping Cloudflare purge."
  echo "    Purge manually at: https://dash.cloudflare.com"
else
  curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/purge_cache" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"purge_everything":true}' \
    | python3 -c "import sys,json; r=json.load(sys.stdin); print('    Cloudflare purge:', 'OK' if r['success'] else r['errors'])"
fi

echo "==> Done."
