#!/usr/bin/env bash
# Stops containers but KEEPS Kafka data. Use "./scripts/stop.sh --purge" to also delete the volume.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "${1:-}" = "--purge" ]; then
  read -r -p "This deletes all Kafka data. Type 'yes' to continue: " ans
  [ "$ans" = "yes" ] || { echo "Aborted."; exit 1; }
  docker compose down -v
else
  docker compose down
fi
