import re
import time
from typing import List

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.models import Product
from scrapers.base import BaseScraper


class JDSportsScraper(BaseScraper):
    """Scrapes product listings from JD Sports.

    Strategy:
    1. Collect sub-categories from the main category page.
    2. For each sub-category, paginate through all product cards.
    3. For each product card, open the detail page to collect sizes.

    All CSS selectors, limits and shop metadata come from the YAML config.
    """

    def scrape_category(self, url: str, category: str) -> List[Product]:
        sel = self._cfg["selectors"]
        driver_cfg = self._cfg.get("driver", {})
        max_products = self._cfg.get("max_products_per_category", 100)

        driver = self._driver_factory.create()
        products: List[Product] = []

        try:
            driver.get(url)
            time.sleep(driver_cfg.get("initial_delay", 2))

            count = 0
            while count < max_products:
                self._load_full_page(driver)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                cards = soup.select(sel["product_item"])

                for card in cards:
                    if count >= max_products:
                        break
                    try:
                        product = self._parse_card(card, category)
                        if product:
                            product = self._enrich_with_sizes(driver, product, sel, driver_cfg)
                            products.append(product)
                            count += 1
                    except Exception as exc:
                        print(f"[JDSports] Error parsing card: {exc}")

                # Try to go to the next page
                if not self._go_next_page(driver, sel, driver_cfg):
                    break

        finally:
            driver.quit()

        return products

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_full_page(self, driver) -> None:
        """Click the 'load more' button until it disappears."""
        sel = self._cfg["selectors"]
        while True:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel.get("load_more_btn", "span.btn.rppLnk.showMore"))
                if btn.is_displayed():
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1.5)
                else:
                    break
            except Exception:
                break

    def _go_next_page(self, driver, sel: dict, driver_cfg: dict) -> bool:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel.get("next_page_btn", "a.btn.pageNav[rel='next']"))
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(driver_cfg.get("page_delay", 2))
                return True
        except Exception:
            pass
        return False

    def _parse_card(self, card, category: str) -> Product | None:
        sel = self._cfg["selectors"]
        base_url = self._cfg["base_url"]

        title_tag = card.select_one(sel.get("title", "span.itemTitle a"))
        price_tag = card.select_one(sel.get("price", "span.pri"))
        img_tag = card.select_one(sel.get("image", "img.thumbnail"))

        if not title_tag:
            return None

        href = title_tag.get("href", "")
        ref_item = (base_url + href) if href.startswith("/") else href

        color = self._extract_color_from_url(href)

        return Product(
            title=title_tag.get_text(strip=True),
            category=category,
            size=[],
            color=[color] if color else [],
            price=price_tag.get_text(strip=True) if price_tag else "",
            img_url=img_tag["src"] if img_tag else "",
            ref_item=ref_item,
            shop_id=self._cfg["shop_id"],
            sex=self._cfg["sex"],
        )

    def _enrich_with_sizes(self, driver, product: Product, sel: dict, driver_cfg: dict) -> Product:
        size_wait = driver_cfg.get("size_wait", 15)
        retries = driver_cfg.get("size_retries", 3)

        for _ in range(retries):
            try:
                driver.set_page_load_timeout(40)
                driver.get(product.ref_item)
                WebDriverWait(driver, size_wait).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, sel.get("size_btn", "div#productSizeStock button[data-e2e='pdp-productDetails-size']"))
                    )
                )
                time.sleep(1)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                size_sel = sel.get("size_btn", "div#productSizeStock button[data-e2e='pdp-productDetails-size']")
                product.size = [btn.get("data-size", "") for btn in soup.select(size_sel)]
                return product
            except TimeoutException:
                driver.execute_script("window.stop();")
                time.sleep(1)
            except Exception as exc:
                print(f"[JDSports] Error fetching sizes for {product.ref_item}: {exc}")
                time.sleep(1)

        product.size = []
        return product

    @staticmethod
    def _extract_color_from_url(url: str) -> str:
        match = re.search(r"/product/([a-zA-Zäöüß-]+)-", url)
        if match:
            return match.group(1).split("-")[0].capitalize()
        return ""
