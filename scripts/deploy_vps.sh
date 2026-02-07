#!/usr/bin/env bash
set -euo pipefail

# Usage:
# HOSTINGER_TOKEN=... VPS_ID=... SSH_USER=... SSH_KEY=~/.ssh/id_rsa ./scripts/deploy_vps.sh
# Optional: API_DOMAIN=api.example.com

API_URL="https://developers.hostinger.com/api/vps/v1"

if [[ -z "${HOSTINGER_TOKEN:-}" ]]; then
  echo "HOSTINGER_TOKEN is required" >&2
  exit 1
fi
if [[ -z "${VPS_ID:-}" ]]; then
  echo "VPS_ID is required" >&2
  exit 1
fi
if [[ -z "${SSH_USER:-}" ]]; then
  echo "SSH_USER is required" >&2
  exit 1
fi
if [[ -z "${SSH_KEY:-}" ]]; then
  echo "SSH_KEY is required" >&2
  exit 1
fi

VPS_JSON=$(curl -s "${API_URL}/virtual-machines/${VPS_ID}" \
  -H "Authorization: Bearer ${HOSTINGER_TOKEN}" \
  -H "Content-Type: application/json")

VPS_IP=$(echo "$VPS_JSON" | python - <<'PY'
import json,sys
obj=json.loads(sys.stdin.read())
# hostinger usually returns ip in data.ip or data.main_ip
ip = None
for key in ("ip", "main_ip"):
    if isinstance(obj, dict):
        data = obj.get("data", obj)
        if isinstance(data, dict) and data.get(key):
            ip = data[key]
            break
print(ip or "")
PY
)

if [[ -z "$VPS_IP" ]]; then
  echo "Could not determine VPS IP from Hostinger API response" >&2
  exit 1
fi

BUILD_DIR=$(mktemp -d)
ARCHIVE="${BUILD_DIR}/ask-mirror-talk.tar.gz"

# Create a deploy bundle
( 
  cd "$(dirname "$0")/.." 
  tar --exclude='.venv' --exclude='__pycache__' --exclude='data' -czf "$ARCHIVE" .
)

# Copy bundle to server
scp -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new "$ARCHIVE" "${SSH_USER}@${VPS_IP}:/tmp/ask-mirror-talk.tar.gz"

# Install Docker if needed and deploy
ssh -i "$SSH_KEY" "${SSH_USER}@${VPS_IP}" <<'REMOTE'
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi

if ! command -v docker compose >/dev/null 2>&1; then
  apt-get update && apt-get install -y docker-compose-plugin
fi

mkdir -p /opt/ask-mirror-talk
cd /opt/ask-mirror-talk

tar -xzf /tmp/ask-mirror-talk.tar.gz -C /opt/ask-mirror-talk

# Add env file if not present
if [[ ! -f .env ]]; then
  cp .env.example .env
fi

# Bring up services
/usr/bin/docker compose -f docker-compose.prod.yml up -d --build
REMOTE

echo "Deployed to VPS IP: ${VPS_IP}"
if [[ -n "${API_DOMAIN:-}" ]]; then
  echo "Remember to point DNS A record for ${API_DOMAIN} to ${VPS_IP}"
fi
