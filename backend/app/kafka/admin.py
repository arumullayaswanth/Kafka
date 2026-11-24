from confluent_kafka.admin import AdminClient

from app.config import CONSUMER_GROUPS, settings

_admin: AdminClient | None = None


def _client() -> AdminClient:
    global _admin
    if _admin is None:
        _admin = AdminClient({"bootstrap.servers": settings.kafka_bootstrap})
    return _admin


def describe_assignments() -> dict:
    """Ask Kafka which member of each consumer group owns which partition.
    Returns {group: {client_id: [partitions]}}. Blocking; call from a worker thread."""
    futures = _client().describe_consumer_groups(CONSUMER_GROUPS, request_timeout=5)
    result = {}
    for group, future in futures.items():
        try:
            desc = future.result()
        except Exception:
            result[group] = {}
            continue
        members = {}
        for m in desc.members:
            parts = [tp.partition for tp in (m.assignment.topic_partitions if m.assignment else [])
                     if tp.topic == settings.topic]
            members[m.client_id] = sorted(parts)
        result[group] = dict(sorted(members.items()))
    return result
