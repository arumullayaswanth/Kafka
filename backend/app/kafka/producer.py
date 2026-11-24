import json
import threading
from typing import Optional

from confluent_kafka import KafkaException, Producer

from app.config import settings


class KafkaPublisher:
    """Thin wrapper around confluent_kafka.Producer with a blocking publish()."""

    def __init__(self):
        self._producer: Optional[Producer] = None
        self._stop = threading.Event()

    def start(self):
        self._producer = Producer({
            "bootstrap.servers": settings.kafka_bootstrap,
            "client.id": "orders-backend",
            "acks": "all",
            "enable.idempotence": True,
            "message.timeout.ms": 10000,
        })
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def stop(self):
        self._stop.set()
        if self._producer:
            self._producer.flush(5)

    def _poll_loop(self):
        while not self._stop.is_set():
            self._producer.poll(0.2)  # serves delivery callbacks

    def check(self, timeout: float = 3):
        """Raises if the broker or topic is unreachable."""
        self._producer.list_topics(settings.topic, timeout)

    def publish(self, key: str, payload: dict) -> dict:
        """Blocking. Returns {partition, offset} or {error}. Call from a worker thread."""
        done = threading.Event()
        result: dict = {}

        def callback(err, msg):
            if err is not None:
                result["error"] = str(err)
            else:
                result["partition"], result["offset"] = msg.partition(), msg.offset()
            done.set()

        try:
            self._producer.produce(settings.topic, key=key, value=json.dumps(payload), callback=callback)
        except (BufferError, KafkaException) as exc:
            return {"error": str(exc)}
        if not done.wait(12):
            return {"error": "timed out waiting for broker acknowledgement"}
        return result


publisher = KafkaPublisher()
