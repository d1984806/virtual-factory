from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppPaths:
    root: Path
    data_dir: Path
    exports_dir: Path
    logs_dir: Path
    db_path: Path
    price_cache_path: Path


DEFAULT_DB_NAME = "robo.db"


def load_environment() -> None:
    load_dotenv()


def build_paths(base_dir: Path) -> AppPaths:
    data_dir = base_dir / "data"
    exports_dir = base_dir / "exports"
    logs_dir = base_dir / "logs"
    db_path = data_dir / DEFAULT_DB_NAME
    price_cache_path = data_dir / "price_cache.json"
    return AppPaths(
        root=base_dir,
        data_dir=data_dir,
        exports_dir=exports_dir,
        logs_dir=logs_dir,
        db_path=db_path,
        price_cache_path=price_cache_path,
    )


def ensure_directories(paths: AppPaths) -> None:
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    paths.exports_dir.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)
