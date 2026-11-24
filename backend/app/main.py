import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.kafka.producer import publisher
from app.routes import health, orders
from app.services.order_service import watch_assignments


@asynccontextmanager
async def lifespan(app: FastAPI):
    publisher.start()
    watcher = asyncio.create_task(watch_assignments())
    yield
    watcher.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await watcher
    publisher.stop()


app = FastAPI(title="Orders API", lifespan=lifespan)
app.include_router(health.router)
app.include_router(orders.router)
