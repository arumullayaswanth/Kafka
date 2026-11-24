#!/usr/bin/env bash
# Creates .env (with a random INTERNAL_API_TOKEN) if missing, then builds and starts everything.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  sed -i "s/^INTERNAL_API_TOKEN=.*/INTERNAL_API_TOKEN=$(openssl rand -hex 24)/" .env
  echo "Created .env with a generated INTERNAL_API_TOKEN"
fi

docker compose up -d --build
docker compose ps
echo
echo "Shop:     http://<EC2-PUBLIC-IP>:${FRONTEND_PORT:-80}"
echo "Kafka UI: http://<EC2-PUBLIC-IP>:${KAFKA_UI_PORT:-8080}"
