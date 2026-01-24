from pydantic import BaseModel


class SizeComparison(BaseModel):
    size: str
    eu_size: str | None = None  # EU Size 추가
    color: str
    
    # Musinsa Info
    musinsa_price: int
    musinsa_stock_status: str  # IN_STOCK, OUT_OF_STOCK
    musinsa_url: str | None = None
    
    # Poizon Info
    poizon_price: int
    poizon_stock_status: str
    poizon_url: str | None = None
    
    # Analysis (Arbitrage Perspective: Buy at Musinsa, Sell at Poizon)
    price_diff: int  # Poizon - Musinsa (Positive means profit)
    is_profitable: bool  # True if price_diff > 0
    profit_margin: float = 0.0  # (price_diff / musinsa_price) * 100


class ProductComparisonResult(BaseModel):
    keyword: str
    musinsa_title: str
    poizon_title: str
    image_url: str
    poizon_sales_score: float = 0.0  # Poizon 판매 지수 추가
    poizon_sales_rank: str = "N/A"   # Poizon 판매 등급 추가
    comparisons: list[SizeComparison]
