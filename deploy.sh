#!/bin/bash
# Deployment script for gohifun / lovesupplychain.com
#
# == HOW TO DEPLOY ==
# 1. SSH into the VPS:
#      ssh root@185.230.218.76
#    (enter root password when prompted)
#
# 2. Pull latest code and restart the service:
#      cd /home/gohifun && git pull origin main && sudo systemctl restart gohifun.service
#
# 3. If static assets changed, run this script on the server:
#      cd /home/gohifun && bash deploy.sh
# ==================

set -e

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
    --data '{"prefixes":["lovesupplychain.com/static/"]}' \
    | python3 -c "import sys,json; r=json.load(sys.stdin); print('    Cloudflare purge:', 'OK' if r['success'] else r['errors'])"
fi

echo "==> Done."
