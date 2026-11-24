import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    kafka_bootstrap: str
    topic: str
    internal_token: str
    max_orders: int = 100
    max_events: int = 300


settings = Settings(
    kafka_bootstrap=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    topic=os.getenv("TOPIC_NAME", "orders"),
    internal_token=os.environ["INTERNAL_API_TOKEN"],
)

# Server-side catalog: prices are never taken from the client.
CATALOG = {
    "laptop": {"name": "Laptop", "price": 55000},
    "smartphone": {"name": "Smartphone", "price": 24000},
    "headphones": {"name": "Headphones", "price": 3500},
    "keyboard": {"name": "Keyboard", "price": 1800},
    "monitor": {"name": "Monitor", "price": 12000},
}

CONSUMER_GROUPS = ["order-processing-group", "payment-processing-group", "notification-group"]

# Which order field each consumer-group status updates.
STAGE_FIELD = {
    "PROCESSED": "status",                       # order-processing-group
    "PAYMENT_CONFIRMED": "payment_status",       # payment-processing-group
    "NOTIFICATION_SENT": "notification_status",  # notification-group
}
