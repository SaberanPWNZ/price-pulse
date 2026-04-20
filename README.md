# price-pulse

A configurable, SOLID-compliant web scraper that collects product data from
online fashion shops and saves the results as JSON files ready to feed a
price-comparison backend.

---

## Features

| Feature | Details |
|---|---|
| **Zero hardcoded values** | Every URL, CSS selector, shop ID and driver option lives in a per-shop YAML config file |
| **SOLID design** | `BaseScraper` → template method; `Storage` → interface; `WebDriverFactory` → DI |
| **Easy to extend** | Add a new shop in three steps: write a config YAML, write a scraper class, register it |
| **CLI** | `--shops`, `--config-dir`, `--output-dir` flags let you customise every run |
| **Supported shops** | Adidas, H&M, Zalando, JD Sports |

---

## Project structure

```
price-pulse/
├── config/               # Per-shop YAML configuration files
│   ├── adidas.yaml
│   ├── hm.yaml
│   ├── jdsports.yaml
│   └── zalando.yaml
├── core/                 # Shared abstractions and utilities
│   ├── driver.py         # WebDriverFactory — creates Selenium Chrome drivers
│   ├── models.py         # Product dataclass
│   └── storage.py        # Storage ABC + JsonStorage implementation
├── scrapers/             # Concrete scrapers, one per shop
│   ├── base.py           # BaseScraper — template method pattern
│   ├── adidas.py
│   ├── hm.py
│   ├── jdsports.py
│   ├── zalando.py
│   └── registry.py       # Maps shop names → scraper classes
├── output/               # JSON output files (git-ignored)
├── main.py               # CLI entry point
├── requirements.txt
└── .env.example
```

---

## Quick start

### 1. Prerequisites

* Python 3.11+
* Google Chrome or Chromium
* `chromedriver` matching your Chrome version and on your `PATH`

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run

```bash
# Scrape all configured shops
python main.py

# Scrape only Adidas and Zalando
python main.py --shops adidas zalando

# Use a different config or output directory
python main.py --config-dir my_configs/ --output-dir results/
```

Results are written to `output/<shop_id>.json` (e.g. `output/2.json` for Adidas).

---

## Output format

Each JSON file contains a list of objects:

```json
[
  {
    "title": "Tiro 24 Training Jacket",
    "category": "training-jackets",
    "size": ["XS", "S", "M", "L", "XL"],
    "color": ["Black", "White"],
    "price": "44,95 €",
    "img_url": "https://...",
    "ref_item": "https://www.adidas.de/...",
    "shop_id": 2,
    "sex": 1,
    "description": null
  }
]
```

Field reference:

| Field | Type | Description |
|---|---|---|
| `title` | `str` | Product name |
| `category` | `str` | Category label from the config |
| `size` | `list[str]` | Available sizes |
| `color` | `list[str]` | Available colours |
| `price` | `str` | Price string as displayed on the site |
| `img_url` | `str` | Product image URL |
| `ref_item` | `str` | Product page URL |
| `shop_id` | `int` | Numeric shop identifier from the config |
| `sex` | `int` | 0 = women, 1 = men, 2 = unisex |
| `description` | `str\|null` | Optional description |

---

## Adding a new shop

### 1. Create a config file — `config/myshop.yaml`

```yaml
name: "My Shop"
shop_id: 99
sex: 2
base_url: "https://www.myshop.com"

urls:
  "https://www.myshop.com/clothing/": "clothing"

selectors:
  product_grid: "ul.products li"
  title:        "h2.product-title"
  price:        "span.price"
  link:         "a.product-link"
  image:        "img.product-image"

driver:
  headless:      true
  window_size:   "1920,1080"
  initial_delay: 3
  scroll_delay:  2
```

### 2. Create a scraper — `scrapers/myshop.py`

```python
from typing import List
from core.models import Product
from scrapers.base import BaseScraper

class MyShopScraper(BaseScraper):
    def scrape_category(self, url: str, category: str) -> List[Product]:
        sel = self._cfg["selectors"]
        soup = self._get_soup_with_scroll(url, initial_delay=self._cfg["driver"]["initial_delay"])
        products = []
        for card in soup.select(sel["product_grid"]):
            title_tag = card.select_one(sel["title"])
            # ... extract fields ...
            products.append(Product(...))
        return products
```

### 3. Register the scraper — `scrapers/registry.py`

```python
from scrapers.myshop import MyShopScraper

REGISTRY: dict[str, type[BaseScraper]] = {
    ...
    "myshop": MyShopScraper,
}
```

That's it — run `python main.py --shops myshop`.

---

## Design principles (SOLID)

| Principle | How it is applied |
|---|---|
| **S** — Single Responsibility | `WebDriverFactory` only builds drivers; `JsonStorage` only handles persistence; each scraper only parses one shop |
| **O** — Open/Closed | New shops are added by creating new files — no existing code is modified |
| **L** — Liskov Substitution | Any `BaseScraper` subclass can replace another as a `BaseScraper` |
| **I** — Interface Segregation | `Storage` exposes only `save` and `load`; scrapers depend only on `BaseScraper` |
| **D** — Dependency Inversion | `BaseScraper` depends on `WebDriverFactory` and `Storage` abstractions injected at construction time |
