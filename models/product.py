from typing import Any
from pydantic import BaseModel, Field


class SalesMetrics(BaseModel):
    velocity_score: float
    rank: str
    recent_sales_count: int
    last_sold_time: str | None = None


class ProductOption(BaseModel):
    sku_id: str
    size: str
    color: str
    price: int
    currency: str = "KRW"
    stock_status: str = "IN_STOCK"
    image_url: str | None = None

    kr_leak_price: int | None = None
    cn_leak_price: int | None = None
    is_cheaper_in: str | None = None

    extra_ids: dict[str, str] = Field(default_factory=dict)


class ProductInfo(BaseModel):
    platform: str
    model_no: str
    title: str
    image_url: str
    product_url: str | None = None

    options: list[ProductOption]
    sales_metrics: SalesMetrics | None = None
