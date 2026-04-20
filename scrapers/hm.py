import json
from typing import List

from core.models import Product
from scrapers.base import BaseScraper


class HMScraper(BaseScraper):
    """Scrapes product pages from H&M.

    Strategy:
    1. Collect all product links from the listing page.
    2. For each link, open the product page and extract data from the
       embedded ``__NEXT_DATA__`` JSON (fast, no extra requests).
    3. Fall back to HTML selectors when the JSON is absent.

    All selectors and settings come from the YAML config.
    """

    def scrape_category(self, url: str, category: str) -> List[Product]:
        sel = self._cfg["selectors"]
        driver_cfg = self._cfg.get("driver", {})

        listing_soup = self._get_soup_with_scroll(
            url,
            initial_delay=driver_cfg.get("initial_delay", 5),
            scroll_delay=driver_cfg.get("scroll_delay", 3),
        )

        links = self._collect_links(listing_soup, sel["product_link_pattern"])
        print(f"[H&M] Found {len(links)} product links in '{category}'")

        products: List[Product] = []
        for link in links:
            try:
                product = self._parse_product_page(link, category)
                if product:
                    products.append(product)
            except Exception as exc:
                print(f"[H&M] Error parsing {link}: {exc}")

        return products

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_links(self, soup, link_pattern: str) -> List[str]:
        links: List[str] = []
        base = self._cfg["base_url"]
        for a in soup.select(f"a[href*='{link_pattern}']"):
            href = a.get("href", "")
            full = (base + href.split("?")[0]) if href.startswith("/") else href.split("?")[0]
            if full not in links:
                links.append(full)
        return links

    def _parse_product_page(self, url: str, category: str) -> Product | None:
        sel = self._cfg["selectors"]
        driver_cfg = self._cfg.get("driver", {})

        soup = self._get_soup(url, delay=driver_cfg.get("page_delay", 3))

        data = {
            "title": None,
            "category": category,
            "size": [],
            "color": [],
            "price": None,
            "img_url": None,
        }

        # --- Primary: __NEXT_DATA__ JSON ---
        next_data = soup.find("script", id="__NEXT_DATA__")
        if next_data:
            try:
                json_data = json.loads(next_data.string)
                product = json_data["props"]["pageProps"]["product"]
                data["title"] = product.get("name")
                data["img_url"] = product.get("whitePrice", {}).get("image", {}).get("url")
                data["price"] = (
                    product.get("whitePrice", {}).get("formattedValue")
                    or product.get("redPrice", {}).get("formattedValue")
                )
                data["category"] = product.get("categoryName") or product.get("mainCategoryCode") or category
                data["color"] = list(
                    {
                        v.get("rgbColors", [{}])[0].get("hex", "")
                        for v in product.get("variantsList", [])
                        if v.get("rgbColors")
                    }
                    - {""}
                )
                data["size"] = [
                    s.get("name")
                    for s in product.get("sizes", [])
                    if s.get("name")
                ]
            except (json.JSONDecodeError, KeyError):
                pass  # fall through to HTML fallback

        # --- Fallback: HTML selectors ---
        if not data["title"]:
            tag = soup.select_one(sel.get("title", "h1"))
            if not tag:
                tag = soup.select_one("meta[property='og:title']")
                data["title"] = tag["content"] if tag else None
            else:
                data["title"] = tag.get_text(strip=True)

        if not data["price"]:
            tag = soup.find("span", string=lambda s: s and "€" in s)
            data["price"] = tag.get_text(strip=True) if tag else ""

        if not data["color"]:
            color_sel = sel.get("color", "")
            if color_sel:
                data["color"] = [
                    el.get("title") or el.get("alt", "")
                    for el in soup.select(color_sel)
                ]

        if not data["size"]:
            size_sel = sel.get("size", "")
            if size_sel:
                data["size"] = [
                    div.get_text(strip=True)
                    for div in soup.find_all("div", attrs={"aria-label": lambda v: v and size_sel in v})
                    if div.get_text(strip=True)
                ]

        if not data["img_url"]:
            tag = soup.select_one("meta[property='og:image']")
            data["img_url"] = tag["content"] if tag else ""

        if not data["title"]:
            return None

        return Product(
            title=data["title"],
            category=data["category"],
            size=data["size"],
            color=data["color"],
            price=data["price"] or "",
            img_url=data["img_url"] or "",
            ref_item=url,
            shop_id=self._cfg["shop_id"],
            sex=self._cfg["sex"],
        )
