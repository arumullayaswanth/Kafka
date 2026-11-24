import asyncio
import uuid
from collections import OrderedDict, deque
from datetime import datetime, timezone

from fastapi.concurrency import run_in_threadpool

from app.config import CATALOG, STAGE_FIELD, settings
from app.kafka.admin import describe_assignments
from app.kafka.producer import publisher
from app.models.order import OrderRequest, ProcessedEvent


class PublishError(Exception):
    pass


# In-memory state. All mutations happen on the event loop (no locking needed).
orders: "OrderedDict[str, dict]" = OrderedDict()
events: deque = deque(maxlen=settings.max_events)
assignments: dict = {}  # group -> {consumer -> [partitions]}
clients: set = set()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def list_orders(limit: int = 20) -> list:
    return list(reversed(list(orders.values())))[:limit]


def list_events(limit: int = 50) -> list:
    return list(reversed(events))[:limit]


def list_assignments() -> dict:
    return {g: dict(sorted(c.items())) for g, c in sorted(assignments.items())}


def _remember(order: dict):
    orders[order["order_id"]] = order
    orders.move_to_end(order["order_id"])
    while len(orders) > settings.max_orders:
        orders.popitem(last=False)


def _new_order(order_id, customer, product, amount, created) -> dict:
    return {
        "order_id": order_id, "customer_name": customer, "product": product, "amount": amount,
        "status": "PUBLISHING", "payment_status": "PENDING", "notification_status": "PENDING",
        "created_at": created, "partition": None, "offset": None,
        "processed_by": {},  # group -> consumer name
    }


async def broadcast(message: dict):
    dead = []
    for ws in list(clients):
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)


async def _record_event(order: dict, event_status: str, partition=None, offset=None, group=None, consumer=None):
    event = {
        "order_id": order["order_id"],
        "customer_name": order["customer_name"],
        "product": order["product"],
        "amount": order["amount"],
        "event_status": event_status,
        "group": group,
        "consumer": consumer,
        "timestamp": now(),
        "partition": partition,
        "offset": offset,
    }
    events.append(event)
    await broadcast({"type": "update", "order": order, "event": event})


async def place_order(req: OrderRequest) -> dict:
    """Validates, publishes to Kafka (key = order_id) and returns the publish result.
    Raises ValueError for invalid input and PublishError if Kafka did not acknowledge."""
    ids = [i.product_id for i in req.items]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate products in order")
    unknown = [i for i in ids if i not in CATALOG]
    if unknown:
        raise ValueError(f"unknown product(s): {', '.join(unknown)}")

    lines = [
        {"product": CATALOG[i.product_id]["name"], "quantity": i.quantity,
         "unit_price": CATALOG[i.product_id]["price"]}
        for i in req.items
    ]
    amount = sum(l["quantity"] * l["unit_price"] for l in lines)
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    created = now()
    summary = ", ".join(f"{l['product']} x{l['quantity']}" for l in lines)
    customer = req.customer_name.strip()

    payload = {
        "order_id": order_id, "customer_name": customer, "items": lines, "product": summary,
        "amount": amount, "status": "ORDER_PLACED", "created_at": created,
    }
    order = _new_order(order_id, customer, summary, amount, created)
    _remember(order)

    result = await run_in_threadpool(publisher.publish, order_id, payload)
    if "error" in result:
        order["status"] = "FAILED"
        await _record_event(order, "PUBLISH_FAILED")
        raise PublishError(f"order {order_id} could not be published: {result['error']}")

    order.update(status="PUBLISHED", partition=result["partition"], offset=result["offset"])
    await _record_event(order, "ORDER_PUBLISHED", result["partition"], result["offset"], group="producer", consumer="backend")
    return {
        "order_id": order_id, "customer_name": customer, "publish_status": "PUBLISHED",
        "topic": settings.topic, "partition": result["partition"], "offset": result["offset"],
        "amount": amount,
    }


async def mark_processed(ev: ProcessedEvent):
    order = orders.get(ev.order_id)
    if order is None:  # e.g. replayed message from before a backend restart
        order = _new_order(ev.order_id, ev.customer_name, ev.product, ev.amount, now())
        order.update(status="PUBLISHED", partition=ev.partition, offset=ev.offset)
        _remember(order)
    order[STAGE_FIELD[ev.status]] = ev.status
    order["processed_by"][ev.group] = ev.consumer
    await _record_event(order, ev.status, ev.partition, ev.offset, ev.group, ev.consumer)


async def watch_assignments(interval: float = 3.0):
    """Polls Kafka for consumer group membership and pushes changes to browsers.
    Kafka is the source of truth, so this stays correct after backend restarts."""
    global assignments
    while True:
        try:
            latest = await run_in_threadpool(describe_assignments)
            if latest != assignments:
                assignments = latest
                await broadcast({"type": "assignments", "assignments": list_assignments()})
        except Exception as exc:  # broker briefly unavailable; try again next round
            print(f"[WARN] assignment poll failed: {exc}", flush=True)
        await asyncio.sleep(interval)
