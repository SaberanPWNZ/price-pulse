#!/usr/bin/env python3
"""
price-pulse — configurable shop scraper
========================================

Usage
-----
  # Scrape all configured shops
  python main.py

  # Scrape specific shops
  python main.py --shops adidas zalando

  # Use a custom config directory
  python main.py --config-dir my_configs/

  # Use a custom output directory
  python main.py --output-dir results/

Run ``python main.py --help`` for full options.
"""

import argparse
import os
import sys

import yaml

from core.driver import WebDriverFactory
from core.storage import JsonStorage
from scrapers.registry import REGISTRY


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="price-pulse: scrape product data from online shops",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--shops",
        nargs="*",
        default=None,
        metavar="SHOP",
        help=(
            "Names of shops to scrape (space-separated). "
            f"Available: {', '.join(sorted(REGISTRY))}. "
            "Omit to scrape all configured shops."
        ),
    )
    parser.add_argument(
        "--config-dir",
        default="config",
        metavar="DIR",
        help="Directory that contains per-shop YAML config files (default: config/).",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        metavar="DIR",
        help="Directory where JSON result files are written (default: output/).",
    )
    return parser


def discover_configs(config_dir: str, requested: list[str] | None) -> list[tuple[str, dict]]:
    """Return a list of (shop_key, config_dict) pairs.

    If *requested* is None every YAML file found in *config_dir* is loaded.
    Otherwise only the listed shop names are loaded.
    """
    configs = []
    for fname in sorted(os.listdir(config_dir)):
        if not fname.endswith(".yaml"):
            continue
        shop_key = fname.replace(".yaml", "")
        if requested is not None and shop_key not in requested:
            continue
        if shop_key not in REGISTRY:
            print(f"[main] No scraper registered for '{shop_key}' — skipping.")
            continue
        path = os.path.join(config_dir, fname)
        configs.append((shop_key, load_config(path)))
    return configs


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.shops is not None:
        unknown = set(args.shops) - set(REGISTRY)
        if unknown:
            print(f"[main] Unknown shop(s): {', '.join(sorted(unknown))}")
            print(f"[main] Available: {', '.join(sorted(REGISTRY))}")
            sys.exit(1)

    shop_configs = discover_configs(args.config_dir, args.shops)
    if not shop_configs:
        print("[main] No configs found. Nothing to scrape.")
        sys.exit(0)

    storage = JsonStorage(args.output_dir)

    for shop_key, cfg in shop_configs:
        scraper_cls = REGISTRY[shop_key]
        driver_factory = WebDriverFactory.from_config(cfg.get("driver", {}))
        scraper = scraper_cls(cfg, driver_factory, storage)
        print(f"\n{'=' * 60}")
        print(f"  Scraping: {cfg.get('name', shop_key)}")
        print(f"{'=' * 60}")
        products = scraper.run()
        print(f"[main] Done — {len(products)} products saved for '{cfg.get('name', shop_key)}'")

    print("\n[main] All scrapers finished.")


if __name__ == "__main__":
    main()
