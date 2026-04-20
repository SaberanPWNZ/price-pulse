import json
import os
from abc import ABC, abstractmethod
from typing import List

from core.models import Product


class Storage(ABC):
    """Abstract storage interface.

    Interface Segregation: only two methods are required — ``save`` and
    ``load``.  Concrete implementations decide the serialisation format.
    """

    @abstractmethod
    def save(self, products: List[Product], identifier: str) -> None:
        """Persist *products* under the given *identifier* (e.g. shop name)."""

    @abstractmethod
    def load(self, identifier: str) -> List[Product]:
        """Load previously saved products for *identifier*."""


class JsonStorage(Storage):
    """Saves / loads products as a JSON file inside *output_dir*.

    The file is named ``<identifier>.json``.  If the file already exists
    its contents are replaced, not appended (idempotent re-runs).
    """

    def __init__(self, output_dir: str) -> None:
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _path(self, identifier: str) -> str:
        return os.path.join(self._output_dir, f"{identifier}.json")

    def save(self, products: List[Product], identifier: str) -> None:
        path = self._path(identifier)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([p.to_dict() for p in products], fh, ensure_ascii=False, indent=2)
        print(f"[Storage] Saved {len(products)} products → {path}")

    def load(self, identifier: str) -> List[Product]:
        path = self._path(identifier)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        return [
            Product(
                title=r["title"],
                category=r["category"],
                price=r["price"],
                img_url=r["img_url"],
                ref_item=r["ref_item"],
                shop_id=r["shop_id"],
                sex=r["sex"],
                size=r.get("size", []),
                color=r.get("color", []),
                description=r.get("description"),
            )
            for r in raw
        ]
