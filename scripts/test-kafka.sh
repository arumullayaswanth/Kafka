#!/usr/bin/env bash
# End-to-end test: 5 customers place orders, all 3 consumer groups must process every order,
# each group must have 3 members owning one partition each.
# Works on Linux/EC2 and in Git Bash on Windows.
set -euo pipefail
cd "$(dirname "$0")/.."
BASE="${BASE_URL:-http://localhost:${FRONTEND_PORT:-80}}"
TOPIC="${TOPIC_NAME:-orders}"
GROUPS_LIST="order-processing-group payment-processing-group notification-group"

# Run a Kafka CLI tool inside the broker container. MSYS_NO_PATHCONV stops Git Bash
# from rewriting /opt/... into C:/Program Files/Git/opt/... (scoped to docker only).
kafka() { MSYS_NO_PATHCONV=1 docker compose exec -T kafka "/opt/kafka/bin/$1" "${@:2}"; }

# On Windows "python3" is often a Microsoft Store stub; fall back to "python".
PY=python3; $PY -c "" 2>/dev/null || PY=python

echo "1. Health"
curl -fsS "$BASE/health"; echo

echo "2. Five customers place orders"
IDS=""
for pair in "Customer 1:laptop" "Customer 2:smartphone" "Customer 3:headphones" "Customer 4:keyboard" "Customer 5:monitor"; do
  name="${pair%%:*}"; product="${pair##*:}"
  RESP=$(curl -fsS -X POST "$BASE/api/orders" -H 'Content-Type: application/json' \
    -d "{\"customer_name\":\"$name\",\"items\":[{\"product_id\":\"$product\",\"quantity\":1}]}")
  echo "  $RESP"
  IDS="$IDS $(echo "$RESP" | $PY -c 'import sys,json;print(json.load(sys.stdin)["order_id"])')"
done

echo "3. Invalid order is rejected (expect 422)"
code=$(curl -s -w '\n%{http_code}' -X POST "$BASE/api/orders" -H 'Content-Type: application/json' \
  -d '{"customer_name":"A","items":[{"product_id":"car","quantity":1}]}' | tail -n 1)
echo "  HTTP $code"; [ "$code" = "422" ]

echo "4. Wait until all 3 groups processed all 5 orders"
CHECK="
import sys, json
want = set(sys.argv[1].split())
orders = {o['order_id']: o for o in json.load(sys.stdin) if o['order_id'] in want}
done = [o for o in orders.values() if o['status'] == 'PROCESSED'
        and o['payment_status'] == 'PAYMENT_CONFIRMED' and o['notification_status'] == 'NOTIFICATION_SENT']
print(len(done))
"
n=0
for _ in $(seq 1 30); do
  n=$(curl -fsS "$BASE/api/orders?limit=100" | $PY -c "$CHECK" "$IDS")
  [ "$n" = "5" ] && break; sleep 1
done
echo "  fully processed: $n/5"; [ "$n" = "5" ]
curl -fsS "$BASE/api/orders?limit=100" | $PY -c "
import sys, json
want = set(sys.argv[1].split())
for o in json.load(sys.stdin):
    if o['order_id'] in want:
        b = o['processed_by']
        print(f\"  {o['order_id']} {o['customer_name']:<11} P{o['partition']}  order={b.get('order-processing-group')}  payment={b.get('payment-processing-group')}  notify={b.get('notification-group')}\")
" "$IDS"

echo "5. Internal endpoint not reachable through the frontend (expect 404 or 405)"
code=$(curl -s -w '\n%{http_code}' -X POST "$BASE/internal/events" | tail -n 1)
echo "  HTTP $code"; [ "$code" = "404" ] || [ "$code" = "405" ]

echo "6. Event in Kafka (key = order id)"
FIRST=$(echo $IDS | cut -d' ' -f1)
found=$(kafka kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic "$TOPIC" \
  --from-beginning --timeout-ms 10000 --property print.key=true --property print.partition=true \
  --property print.offset=true 2>/dev/null | grep "$FIRST" | head -n 1 || true)
echo "  $found"; [ -n "$found" ]

echo "7. Each group: 3 members, one partition each"
for g in $GROUPS_LIST; do
  echo "  --- $g"
  out=$(kafka kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group "$g" --members --verbose)
  echo "$out" | sed 's/^/  /'
  # Member rows start with the group name; column 5 is #PARTITIONS.
  members=$(echo "$out" | awk -v g="$g" '$1 == g && $5 == 1' | wc -l | tr -d ' ')
  [ "$members" = "3" ] || { echo "  expected 3 members owning 1 partition each in $g, got $members"; exit 1; }
done

echo "8. Lag per group (expect 0 everywhere)"
for g in $GROUPS_LIST; do
  kafka kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group "$g" \
    | awk -v g="$g" '$1 == g {print "  " $1, "P" $3, "committed=" $4, "end=" $5, "lag=" $6, $NF}'
done

echo; echo "PASSED: 5 orders x 3 consumer groups, 9 consumers active."
