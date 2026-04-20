from typing import List

from core.models import Product
from scrapers.base import BaseScraper


class AdidasScraper(BaseScraper):
    """Scrapes product listings from Adidas.

    All CSS selectors, URLs, shop metadata and driver settings are read from
    the YAML config — nothing is hardcoded in this class.
    """

    def scrape_category(self, url: str, category: str) -> List[Product]:
        sel = self._cfg["selectors"]
        driver_cfg = self._cfg.get("driver", {})

        soup = self._get_soup_with_scroll(
            url,
            initial_delay=driver_cfg.get("initial_delay", 7),
            scroll_delay=driver_cfg.get("scroll_delay", 3),
        )

        cards = soup.select(sel["product_grid"])
        products: List[Product] = []

        for card in cards:
            try:
                title_tag = card.select_one(sel["title"])
                title = title_tag.get_text(strip=True) if title_tag else None

                price_tag = card.select_one(sel["price"])
                price = price_tag.get_text(strip=True) if price_tag else None

                link_tag = card.select_one(sel["link"])
                ref_item = link_tag["href"] if link_tag else None
                if ref_item and not ref_item.startswith("http"):
                    ref_item = self._cfg["base_url"] + ref_item

                img_tag = card.select_one(sel["image"])
                img_url = img_tag["src"] if img_tag else None

                if not title:
                    continue

                products.append(
                    Product(
                        title=title,
                        category=category,
                        size=[],
                        color=[],
                        price=price or "",
                        img_url=img_url or "",
                        ref_item=ref_item or "",
                        shop_id=self._cfg["shop_id"],
                        sex=self._cfg["sex"],
                    )
                )
            except Exception as exc:
                print(f"[Adidas] Error parsing card: {exc}")

        return products
