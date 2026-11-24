#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
TOPIC="${TOPIC_NAME:-orders}"
fail=0

kafka() { MSYS_NO_PATHCONV=1 docker compose exec -T kafka "/opt/kafka/bin/$1" "${@:2}"; }

echo "== Containers =="; docker compose ps

echo; echo "== Broker =="
kafka kafka-broker-api-versions.sh --bootstrap-server kafka:9092 | head -n 1 || fail=1

echo; echo "== Topic: $TOPIC =="
kafka kafka-topics.sh --bootstrap-server kafka:9092 --describe --topic "$TOPIC" || fail=1

echo; echo "== Backend /health =="
curl -fsS "http://localhost:${FRONTEND_PORT:-80}/health" || fail=1; echo

for group in order-processing-group payment-processing-group notification-group; do
  echo; echo "== Consumer group: $group =="
  kafka kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group "$group" || true
done

echo; echo "== Kafka UI =="
code=$( (curl -s -w '\n%{http_code}' "http://localhost:${KAFKA_UI_PORT:-8080}" || true) | tail -n 1)
echo "HTTP $code"; [ "$code" = "200" ] || fail=1

[ $fail -eq 0 ] && echo -e "\nALL CHECKS PASSED" || echo -e "\nSOME CHECKS FAILED"
exit $fail
