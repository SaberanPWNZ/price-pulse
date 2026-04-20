import time
from abc import ABC, abstractmethod
from typing import List

from bs4 import BeautifulSoup

from core.driver import WebDriverFactory
from core.models import Product
from core.storage import Storage


class BaseScraper(ABC):
    """Abstract base class for all shop scrapers.

    Template Method pattern:
    - ``run()`` orchestrates the full scrape lifecycle.
    - ``scrape_category()`` is the only method subclasses *must* implement.
    - Helper methods (``_get_soup``, ``_scroll_to_bottom``) are provided as
      shared utilities but can be overridden when a shop requires different
      behaviour.

    Dependency Inversion: depends on ``WebDriverFactory`` and ``Storage``
    abstractions, not on concrete classes.
    """

    def __init__(
        self,
        shop_config: dict,
        driver_factory: WebDriverFactory,
        storage: Storage,
    ) -> None:
        self._cfg = shop_config
        self._driver_factory = driver_factory
        self._storage = storage

    # ------------------------------------------------------------------
    # Public template method – entry point for callers
    # ------------------------------------------------------------------

    def run(self) -> List[Product]:
        """Scrape all configured URLs and persist the results."""
        all_products: List[Product] = []
        urls: dict = self._cfg.get("urls", {})
        for url, category in urls.items():
            print(f"[{self._cfg['name']}] Scraping category '{category}': {url}")
            try:
                products = self.scrape_category(url, category)
                print(f"[{self._cfg['name']}] Found {len(products)} products in '{category}'")
                all_products.extend(products)
            except Exception as exc:
                print(f"[{self._cfg['name']}] Error scraping '{category}': {exc}")

        self._storage.save(all_products, self._cfg["shop_id"])
        return all_products

    # ------------------------------------------------------------------
    # Abstract hook – must be implemented by every concrete scraper
    # ------------------------------------------------------------------

    @abstractmethod
    def scrape_category(self, url: str, category: str) -> List[Product]:
        """Return a list of :class:`Product` objects scraped from *url*."""

    # ------------------------------------------------------------------
    # Protected helpers available to all subclasses
    # ------------------------------------------------------------------

    def _get_soup(self, url: str, *, delay: float = 0) -> BeautifulSoup:
        """Open *url* in a fresh driver, wait *delay* seconds, return a
        ``BeautifulSoup`` object.  The driver is always closed afterwards."""
        driver = self._driver_factory.create()
        try:
            driver.get(url)
            if delay:
                time.sleep(delay)
            return BeautifulSoup(driver.page_source, "lxml")
        finally:
            driver.quit()

    def _get_soup_with_scroll(self, url: str, *, initial_delay: float = 0, scroll_delay: float = 2) -> BeautifulSoup:
        """Open *url*, wait for JS, scroll to bottom to trigger lazy-loads,
        then return a ``BeautifulSoup``.  The driver is always closed."""
        driver = self._driver_factory.create()
        try:
            driver.get(url)
            if initial_delay:
                time.sleep(initial_delay)
            # Scroll until page height no longer grows
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_delay)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            return BeautifulSoup(driver.page_source, "lxml")
        finally:
            driver.quit()

    @property
    def name(self) -> str:
        return self._cfg.get("name", "unknown")
