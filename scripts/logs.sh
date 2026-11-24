#!/usr/bin/env bash
cd "$(dirname "$0")/.."
exec docker compose logs -f --tail=100 "$@"
