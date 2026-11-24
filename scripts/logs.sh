#!/usr/bin/env bash
# Usage: ./scripts/logs.sh [service ...]   e.g. ./scripts/logs.sh backend consumer
cd "$(dirname "$0")/.."
exec docker compose logs -f --tail=100 "$@"
