from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.config import settings
from app.kafka.producer import publisher

router = APIRouter()


@router.get("/health")
async def health():
    try:
        await run_in_threadpool(publisher.check)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"kafka unavailable: {exc}")
    return {"status": "ok", "kafka": "up", "topic": settings.topic}
