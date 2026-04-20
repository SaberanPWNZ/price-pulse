from typing import List

from core.models import Product
from scrapers.base import BaseScraper


class ZalandoScraper(BaseScraper):
    """Scrapes product listings from Zalando.

    All selectors and shop metadata come from the YAML config.
    """

    def scrape_category(self, url: str, category: str) -> List[Product]:
        sel = self._cfg["selectors"]
        driver_cfg = self._cfg.get("driver", {})

        soup = self._get_soup_with_scroll(
            url,
            initial_delay=driver_cfg.get("initial_delay", 5),
            scroll_delay=driver_cfg.get("scroll_delay", 2),
        )

        product_list = soup.select_one(sel["product_list"])
        if not product_list:
            print(f"[Zalando] Product list not found for '{category}'")
            return []

        products: List[Product] = []
        for item in product_list.select(sel["product_item"]):
            try:
                product = self._parse_card(item, category)
                if product:
                    products.append(product)
            except Exception as exc:
                print(f"[Zalando] Error parsing card: {exc}")

        return products

    def _parse_card(self, card, category: str) -> Product | None:
        sel = self._cfg["selectors"]

        title_tag = card.select_one(sel.get("title", "h3"))
        title = title_tag.get_text(strip=True) if title_tag else None

        price_tag = card.select_one(sel.get("price", "span.price"))
        price = price_tag.get_text(strip=True) if price_tag else ""

        link_tag = card.select_one(sel.get("link", "a[href]"))
        ref_item = link_tag["href"] if link_tag else ""
        if ref_item and not ref_item.startswith("http"):
            ref_item = self._cfg["base_url"] + ref_item

        img_tag = card.select_one(sel.get("image", "img"))
        img_url = img_tag["src"] if img_tag else ""

        if not title:
            return None

        return Product(
            title=title,
            category=category,
            size=[],
            color=[],
            price=price,
            img_url=img_url,
            ref_item=ref_item,
            shop_id=self._cfg["shop_id"],
            sex=self._cfg["sex"],
        )
