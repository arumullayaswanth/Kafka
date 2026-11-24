#!/usr/bin/env bash
# Checks containers, broker, topic, API, consumer group and Kafka UI.
# Works on Linux/EC2 and in Git Bash on Windows.
set -uo pipefail
cd "$(dirname "$0")/.."
TOPIC="${TOPIC_NAME:-orders}"
GROUP="${CONSUMER_GROUP_ID:-order-processing-group}"
fail=0

# MSYS_NO_PATHCONV stops Git Bash from rewriting /opt/... (scoped to docker only).
kafka() { MSYS_NO_PATHCONV=1 docker compose exec -T kafka "/opt/kafka/bin/$1" "${@:2}"; }

echo "== Containers =="; docker compose ps

echo; echo "== Broker =="
kafka kafka-broker-api-versions.sh --bootstrap-server kafka:9092 | head -n 1 || fail=1

echo; echo "== Topic: $TOPIC =="
kafka kafka-topics.sh --bootstrap-server kafka:9092 --describe --topic "$TOPIC" || fail=1

echo; echo "== Backend /health =="
curl -fsS "http://localhost:${FRONTEND_PORT:-80}/health" || fail=1; echo

echo; echo "== Consumer group: $GROUP =="
kafka kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group "$GROUP" || true

echo; echo "== Kafka UI =="
code=$( (curl -s -w '\n%{http_code}' "http://localhost:${KAFKA_UI_PORT:-8080}" || true) | tail -n 1)
echo "HTTP $code"; [ "$code" = "200" ] || fail=1

[ $fail -eq 0 ] && echo -e "\nALL CHECKS PASSED" || echo -e "\nSOME CHECKS FAILED"
exit $fail
