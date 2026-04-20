from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Product:
    """Represents a scraped product from any shop."""

    title: str
    category: str
    price: str
    img_url: str
    ref_item: str
    shop_id: int
    sex: int  # 0 = women, 1 = men, 2 = unisex
    size: List[str] = field(default_factory=list)
    color: List[str] = field(default_factory=list)
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "category": self.category,
            "size": self.size,
            "color": self.color,
            "price": self.price,
            "img_url": self.img_url,
            "ref_item": self.ref_item,
            "shop_id": self.shop_id,
            "sex": self.sex,
            "description": self.description,
        }
