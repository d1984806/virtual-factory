from __future__ import annotations

import logging
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(), logging.FileHandler(log_path, encoding="utf-8")],
    )
