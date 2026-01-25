from abc import ABC, abstractmethod
from typing import Any

class BaseSeller(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def search_product(self, keyword: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def get_product_info(self, product_id: str) -> Any:
        pass
