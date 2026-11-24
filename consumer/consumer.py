"""One consumer program, three roles. CONSUMER_ROLE picks the consumer group and the work done.

    order        -> order-processing-group    -> status PROCESSED
    payment      -> payment-processing-group  -> status PAYMENT_CONFIRMED
    notification -> notification-group        -> status NOTIFICATION_SENT

Every group subscribes to the same "orders" topic, so each group receives every event.
Inside a group, the 3 partitions are split across that group's consumers.
"""
import json
import os
import random
import signal
import socket
import time
import urllib.error
import urllib.request

from confluent_kafka import Consumer, KafkaError, KafkaException

ROLES = {
    "order": {"group": "order-processing-group", "status": "PROCESSED"},
    "payment": {"group": "payment-processing-group", "status": "PAYMENT_CONFIRMED"},
    "notification": {"group": "notification-group", "status": "NOTIFICATION_SENT"},
}

ROLE = os.getenv("CONSUMER_ROLE", "order")
if ROLE not in ROLES:
    raise SystemExit(f"CONSUMER_ROLE must be one of {list(ROLES)}, got {ROLE!r}")

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = os.getenv("TOPIC_NAME", "orders")
GROUP_ID = os.getenv("CONSUMER_GROUP_ID") or ROLES[ROLE]["group"]
DONE_STATUS = ROLES[ROLE]["status"]
NAME = os.getenv("CONSUMER_NAME") or socket.gethostname()
BACKEND_URL = os.getenv("BACKEND_URL", "")  # empty = don't report to backend
INTERNAL_TOKEN = os.getenv("INTERNAL_API_TOKEN", "")

running = True


def log(msg):
    print(f"[{NAME}] {msg}", flush=True)


def stop(signum, frame):
    global running
    running = False


def post(path, body, tries=3):
    """Best-effort report to the backend so the UI updates."""
    if not BACKEND_URL:
        return
    req = urllib.request.Request(
        f"{BACKEND_URL}{path}", data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json", "X-Internal-Token": INTERNAL_TOKEN},
    )
    for attempt in range(1, tries + 1):
        try:
            with urllib.request.urlopen(req, timeout=5):
                return
        except (urllib.error.URLError, OSError) as exc:
            log(f"[WARN] backend {path} failed (try {attempt}/{tries}): {exc}")
            time.sleep(1)


# Assignments are only logged here; the backend reads them from Kafka for the UI.
def on_assign(consumer, partitions):
    log(f"ASSIGNED partitions: {sorted(p.partition for p in partitions)}")


def on_revoke(consumer, partitions):
    log(f"REVOKED partitions: {sorted(p.partition for p in partitions)}")


# ---------- role-specific work (stand-ins for real services) ----------
def process_order(order):
    time.sleep(random.uniform(0.3, 0.8))
    log(f"ORDER    {order['order_id']}: stock reserved for {order.get('product')}")


def process_payment(order):
    time.sleep(random.uniform(0.5, 1.2))
    log(f"PAYMENT  {order['order_id']}: charged {order.get('amount')} to {order.get('customer_name')}")


def send_notification(order):
    time.sleep(random.uniform(0.2, 0.6))
    log(f"NOTIFY   {order['order_id']}: confirmation sent to {order.get('customer_name')}")


HANDLERS = {"order": process_order, "payment": process_payment, "notification": send_notification}


def main():
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    consumer = Consumer({
        "bootstrap.servers": BOOTSTRAP,
        "group.id": GROUP_ID,
        "client.id": NAME,                 # shows up in Kafka UI and kafka-consumer-groups
        "auto.offset.reset": "earliest",   # new group starts from the beginning
        "enable.auto.commit": False,       # commit manually after processing
        "session.timeout.ms": 10000,
    })
    consumer.subscribe([TOPIC], on_assign=on_assign, on_revoke=on_revoke)
    log(f"started role={ROLE} group={GROUP_ID} topic={TOPIC}")

    try:
        while running:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                if msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    log(f"[WARN] topic not available yet: {msg.error()}")
                    continue
                raise KafkaException(msg.error())

            try:
                order = json.loads(msg.value().decode("utf-8"))
                order_id = order["order_id"]
            except (ValueError, KeyError, UnicodeDecodeError) as exc:
                log(f"[ERROR] bad message at partition={msg.partition()} offset={msg.offset()}: {exc}")
                consumer.commit(message=msg, asynchronous=False)  # skip poison message
                continue

            log(f"RECEIVED partition={msg.partition()} offset={msg.offset()} key={order_id}")
            HANDLERS[ROLE](order)
            post("/internal/events", {
                "order_id": order_id,
                "partition": msg.partition(),
                "offset": msg.offset(),
                "status": DONE_STATUS,
                "group": GROUP_ID,
                "consumer": NAME,
                "customer_name": order.get("customer_name", "unknown"),
                "product": order.get("product", ""),
                "amount": order.get("amount", 0),
            })

            # Commit only after the work is done (at-least-once).
            consumer.commit(message=msg, asynchronous=False)
    except KafkaException as exc:
        log(f"[FATAL] {exc}")
        raise
    finally:
        log("closing (leaving group)...")
        consumer.close()


if __name__ == "__main__":
    main()
