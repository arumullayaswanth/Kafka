import json
import threading
from typing import Optional

from confluent_kafka import KafkaException, Producer

from app.config import settings


class KafkaPublisher:

    def __init__(self):
        self._producer: Optional[Producer] = None
        self._stop = threading.Event()  # tells the poll thread to stop

    def start(self):
        self._producer = Producer({
            "bootstrap.servers": settings.kafka_bootstrap,  # kafka:9092
            "client.id": "orders-backend",                  # name shown in Kafka UI
            "acks": "all",                                  # wait until the broker saved it
            "enable.idempotence": True,                     # retries never create duplicates
            "message.timeout.ms": 10000,                    # give up after 10 s
        })
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def stop(self):
        self._stop.set()
        if self._producer:
            self._producer.flush(5)  # send anything still queued

    def _poll_loop(self):
        while not self._stop.is_set():
            self._producer.poll(0.2)  # runs delivery callbacks

    def check(self, timeout: float = 3):
        self._producer.list_topics(settings.topic, timeout)  # fails if Kafka is down

    def publish(self, key: str, payload: dict) -> dict:
        done = threading.Event()
        result: dict = {}

        # Kafka calls this once the message is saved, or failed
        def callback(err, msg):
            if err is not None:
                result["error"] = str(err)
            else:
                result["partition"], result["offset"] = msg.partition(), msg.offset()
            done.set()

        try:
            # key = order_id, so the same order always goes to the same partition
            self._producer.produce(settings.topic, key=key, value=json.dumps(payload), callback=callback)
        except (BufferError, KafkaException) as exc:
            return {"error": str(exc)}
        if not done.wait(12):  # wait for the broker's answer
            return {"error": "timed out waiting for broker acknowledgement"}
        return result  # {"partition": ..., "offset": ...}


publisher = KafkaPublisher()  # one shared producer for the whole app
