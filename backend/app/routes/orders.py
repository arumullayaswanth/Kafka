import secrets

from fastapi import APIRouter, Header, HTTPException, WebSocket, WebSocketDisconnect

from app.config import CATALOG, settings
from app.models.order import OrderRequest, ProcessedEvent
from app.services import order_service as svc

router = APIRouter()


def _check_token(token: str):
    if not secrets.compare_digest(token, settings.internal_token):
        raise HTTPException(401, "invalid token")


@router.get("/api/products")
async def products():
    return [{"id": k, **v} for k, v in CATALOG.items()]


@router.post("/api/orders", status_code=201)
async def create_order(req: OrderRequest):
    try:
        return await svc.place_order(req)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except svc.PublishError as exc:
        raise HTTPException(503, str(exc))


@router.get("/api/orders")
async def recent_orders(limit: int = 20):
    return svc.list_orders(max(1, min(limit, settings.max_orders)))


@router.post("/internal/events")
async def processed(ev: ProcessedEvent, x_internal_token: str = Header(default="")):
    _check_token(x_internal_token)
    await svc.mark_processed(ev)
    return {"ok": True}


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    svc.clients.add(ws)
    try:
        await ws.send_json({
            "type": "snapshot",
            "orders": svc.list_orders(50),
            "events": svc.list_events(100),
            "assignments": svc.list_assignments(),
        })
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        svc.clients.discard(ws)
