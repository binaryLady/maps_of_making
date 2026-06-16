import os
from pathlib import Path

import structlog
import yaml

log = structlog.get_logger()

_config: dict | None = None


def load_config(path: str | None = None) -> dict:
    """Load config.yaml once. Path overridable via CONFIG_PATH env var."""
    global _config
    if _config is not None:
        return _config

    config_path = Path(path or os.environ.get("CONFIG_PATH") or Path(__file__).parent / "config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            _config = yaml.safe_load(f) or {}
    else:
        log.warning("config.yaml not found", path=str(config_path))
        _config = {}
    return _config
