# Architecture

```
Browser ──:80──► frontend (nginx + React build) ──/api, /ws, /health──► backend (FastAPI)
                                                                          │ produce (key = order_id)
                                                                          ▼
Browser ──:8080─► Kafka UI ─────────────────────────────────────────► kafka (KRaft, topic orders P0-P2)
                                                                          │ consume
                                                                          ▼
                                       backend ◄── POST /internal/events ── consumer (order-processing-group)
```

## Services (one shared Compose network)

| Service | Image / build | Published port | Role |
|---|---|---|---|
| kafka | `apache/kafka:3.8.0` | none | Single KRaft node (broker + controller), advertised as `kafka:9092` |
| kafka-init | `apache/kafka:3.8.0` | none | One-shot: runs `kafka/init-topic.sh`, creates `orders` (3 partitions, RF 1) |
| kafka-ui | `provectuslabs/kafka-ui:v0.7.2` | 8080 | Inspect brokers, topics, messages, groups, lag |
| backend | `./backend` (FastAPI) | none | REST + WebSocket, Kafka producer |
| consumer | `./consumer` | none | Group `order-processing-group`, scalable |
| frontend | `./frontend` (Vite build → nginx) | 80 | UI, reverse proxy to backend |

## Order flow

1. The browser sends `POST /api/orders`. nginx forwards it to the backend.
2. The backend validates, prices from its own catalog, generates `ORD-XXXXXXXX`, and publishes with the order ID as key. It waits for the broker ack (`acks=all`, idempotent producer).
3. The response returns order ID, `PUBLISHED`, partition and offset. The UI shows it at once.
4. The consumer reads the message, processes it, reports to `POST /internal/events` (header `X-Internal-Token`), then commits the offset (at-least-once).
5. The backend updates the order to `PROCESSED` and pushes the update to every browser over `/ws`.

## Design notes

- `/internal/*` is not proxied by nginx and requires `INTERNAL_API_TOKEN`, so only containers on the Docker network can post processed events.
- Order state lives in backend memory (last 100 orders). Kafka is the durable store. A backend restart empties the UI lists only.
- Processed events are reported by the consumer over HTTP, so the UI reflects real consumption. The trade-off is a direct consumer→backend dependency. A production design would publish results to a second topic (for example `orders.processed`) that the backend consumes.
- `kafka/config/server.properties` documents the broker settings. The container is configured through the equivalent `KAFKA_*` environment variables in `docker-compose.yml`, which is what the image actually reads.
