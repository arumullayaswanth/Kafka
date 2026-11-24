from typing import Literal

from pydantic import BaseModel, Field

NAME_PATTERN = r"^[A-Za-z0-9 .'_-]+$"


class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=10)


class OrderRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=50, pattern=NAME_PATTERN)
    items: list[OrderItem] = Field(min_length=1, max_length=10)


class ProcessedEvent(BaseModel):
    order_id: str = Field(min_length=1, max_length=64)
    partition: int = Field(ge=0)
    offset: int = Field(ge=0)
    status: Literal["PROCESSED", "PAYMENT_CONFIRMED", "NOTIFICATION_SENT"]
    group: str = Field(min_length=1, max_length=100, pattern=NAME_PATTERN)
    consumer: str = Field(min_length=1, max_length=100, pattern=NAME_PATTERN)
    customer_name: str = Field(default="unknown", max_length=50)
    product: str = Field(default="", max_length=200)
    amount: float = 0

