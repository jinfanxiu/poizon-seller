from abc import ABC, abstractmethod
from models.product import ProductInfo

class BaseSeller(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def search_product(self, keyword: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def get_product_info(self, product_id: str) -> ProductInfo | None:
        pass