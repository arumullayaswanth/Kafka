# Troubleshooting

Start with `docker compose ps`, `./scripts/logs.sh <service>` and `./scripts/health-check.sh`.

| Symptom | Cause and fix |
|---|---|
| `Set INTERNAL_API_TOKEN in .env` on `up` | `.env` missing or token empty. Run `./scripts/start.sh` or fill it with `openssl rand -hex 24`. |
| `kafka` unhealthy / restarting | `./scripts/logs.sh kafka`. Check RAM (`free -m`) and disk (`df -h`). After changing broker config, the old volume can hold stale metadata: `./scripts/stop.sh --purge` (deletes data). |
| `kafka-init` fails | Broker wasn't ready or the topic exists with other settings. `docker compose logs kafka-init`. Re-run: `docker compose up kafka-init`. |
| Advertised listener errors (`Connection to node 1 (localhost/127.0.0.1:9092) could not be established`) | The broker's advertised address must be reachable from the client. Here it is `kafka:9092`, valid only inside the Compose network. Run clients as Compose services. For host clients add a second listener bound to 127.0.0.1. |
| Kafka UI shows cluster offline | `./scripts/logs.sh kafka-ui`. Bootstrap must be `kafka:9092`, not `localhost`. |
| Page doesn't load from your browser | Security group needs ports 80 and 8080 from your current public IP. Test on the server: `curl -I localhost`. |
| Place Order returns 503 | Backend couldn't publish: `./scripts/logs.sh backend`. Check `curl localhost/health` and that the topic exists. |
| Place Order returns 422 | Validation: unknown product, quantity outside 1–10, duplicate product or bad customer name. |
| Orders stay `PUBLISHED` | Consumer isn't running or can't reach the backend. `./scripts/logs.sh order-consumer-1` and look for `backend report failed`. Token mismatch is unlikely since both read `.env`, but a stale container can hold an old token: `docker compose up -d --force-recreate`. |
| UI says "Reconnecting..." | WebSocket blocked. `./scripts/logs.sh frontend backend`. Behind a proxy or load balancer, enable WebSocket upgrade. |
| Topic not visible in Kafka UI | `docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list`, then refresh the UI. |
| Consumer group not in UI | Groups appear after a consumer joins. Wait 10 s. Check the consumers are running: `docker compose ps`. |
| Offset not updating | The consumer commits after each processed message. If it's stopped, the committed offset freezes and lag grows. Compare with `kafka-consumer-groups.sh --describe --group order-processing-group`. |
| Consumer doesn't replay old messages | The group already has committed offsets. Reset: stop the consumer, run `kafka-consumer-groups.sh ... --reset-offsets --to-earliest --execute --topic orders`, start it again. |
| Frontend build fails (`npm install`) | Needs outbound internet and about 1 GB RAM. Add swap on small instances. |
| `bad interpreter` / `\r` errors in scripts | Windows line endings: `sed -i 's/\r$//' scripts/*.sh kafka/*.sh`. |
