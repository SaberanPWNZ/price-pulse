"""
ScraperRegistry — maps shop names to their concrete scraper classes.

Open/Closed principle: to add a new shop, register it here without
touching any other module.
"""

from scrapers.adidas import AdidasScraper
from scrapers.hm import HMScraper
from scrapers.jdsports import JDSportsScraper
from scrapers.zalando import ZalandoScraper
from scrapers.base import BaseScraper

REGISTRY: dict[str, type[BaseScraper]] = {
    "adidas": AdidasScraper,
    "hm": HMScraper,
    "zalando": ZalandoScraper,
    "jdsports": JDSportsScraper,
}
