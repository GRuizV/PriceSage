"""Load the product/vendor configuration (`config/products.yml`)."""

from __future__ import annotations

from pathlib import Path

import yaml

# config/products.yml lives at the project root: src/pricesage/config.py -> root
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "products.yml"


def load_config(path: str | Path | None = None) -> dict:
    """Parse the YAML config into a dict keyed by vendor."""
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
