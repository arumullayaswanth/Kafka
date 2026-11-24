# Architecture

```
Browser ──:80──► frontend (nginx + React build) ──/api, /ws, /health──► backend (FastAPI)
                                                                          │ produce (key = order_id)
                                                                          ▼
Browser ──:8080─► Kafka UI ─────────────────────────────────────────► kafka (KRaft, topic orders P0-P2)
                                                                          │ consume
                                                                          ▼
                                       backend ◄── POST /internal/events ── 9 consumers (3 groups x 3)
```

## Services (one shared Compose network)

| Service | Image / build | Published port | Role |
|---|---|---|---|
| kafka | `apache/kafka:3.8.0` | none | Single KRaft node (broker + controller), advertised as `kafka:9092` |
| kafka-init | `apache/kafka:3.8.0` | none | One-shot: runs `kafka/init-topic.sh`, creates `orders` (3 partitions, RF 1) |
| kafka-ui | `provectuslabs/kafka-ui:v0.7.2` | 8080 | Inspect brokers, topics, messages, groups, lag |
| backend | `./backend` (FastAPI) | none | REST + WebSocket, Kafka producer |
| order/payment/notification-consumer-1..3 | `./consumer` (one image) | none | 9 consumers, 3 per group; `CONSUMER_ROLE` picks the group |
| frontend | `./frontend` (Vite build → nginx) | 80 | UI, reverse proxy to backend |

## Order flow

1. The browser sends `POST /api/orders`. nginx forwards it to the backend.
2. The backend validates, prices from its own catalog, generates `ORD-XXXXXXXX`, and publishes with the order ID as key. It waits for the broker ack (`acks=all`, idempotent producer).
3. The response returns order ID, `PUBLISHED`, partition and offset. The UI shows it at once.
4. Each of the 3 groups reads every message. The consumer that owns the partition processes it, reports to `POST /internal/events` (header `X-Internal-Token`), then commits the offset (at-least-once).
5. The backend updates that group's status (`PROCESSED`, `PAYMENT_CONFIRMED` or `NOTIFICATION_SENT`) and pushes the update to every browser over `/ws`.

## Design notes

- `/internal/*` is not proxied by nginx and requires `INTERNAL_API_TOKEN`, so only containers on the Docker network can post processed events.
- Order state lives in backend memory (last 100 orders). Kafka is the durable store. A backend restart empties the UI lists only.
- Processed events are reported by the consumer over HTTP, so the UI reflects real consumption. The trade-off is a direct consumer→backend dependency. A production design would publish results to a second topic (for example `orders.processed`) that the backend consumes.
- `kafka/config/server.properties` documents the broker settings. The container is configured through the equivalent `KAFKA_*` environment variables in `docker-compose.yml`, which is what the image actually reads.
