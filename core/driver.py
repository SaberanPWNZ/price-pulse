from dataclasses import dataclass
from typing import Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@dataclass
class DriverConfig:
    """Holds all WebDriver configuration — no defaults hardcoded here;
    values come from the per-shop YAML config or CLI overrides."""

    headless: bool
    window_size: Tuple[int, int]
    disable_automation_flag: bool
    no_sandbox: bool
    disable_dev_shm: bool
    binary_location: str = ""  # empty string → use system default


class WebDriverFactory:
    """Creates a Selenium Chrome WebDriver from a DriverConfig.

    Single Responsibility: only responsible for driver construction.
    Open/Closed: to support a different browser, subclass or extend — do not
    modify this class.
    """

    def __init__(self, config: DriverConfig) -> None:
        self._config = config

    def create(self) -> webdriver.Chrome:
        options = Options()

        if self._config.disable_automation_flag:
            options.add_argument("--disable-blink-features=AutomationControlled")
        if self._config.no_sandbox:
            options.add_argument("--no-sandbox")
        if self._config.disable_dev_shm:
            options.add_argument("--disable-dev-shm-usage")

        w, h = self._config.window_size
        options.add_argument(f"--window-size={w},{h}")

        if self._config.headless:
            options.add_argument("--headless")

        if self._config.binary_location:
            options.binary_location = self._config.binary_location

        return webdriver.Chrome(options=options)

    @classmethod
    def from_config(cls, driver_cfg: dict) -> "WebDriverFactory":
        """Build a factory from the ``driver`` section of a shop YAML config."""
        raw_size = driver_cfg.get("window_size", "1920,1080")
        w, h = (int(x) for x in raw_size.split(","))
        config = DriverConfig(
            headless=driver_cfg.get("headless", True),
            window_size=(w, h),
            disable_automation_flag=driver_cfg.get("disable_automation_flag", True),
            no_sandbox=driver_cfg.get("no_sandbox", True),
            disable_dev_shm=driver_cfg.get("disable_dev_shm", True),
            binary_location=driver_cfg.get("binary_location", ""),
        )
        return cls(config)
