"""Gerenciamento de cache em disco com TTL para índices e catálogos."""

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from rom_cli.config import CACHE_DIR


class CacheManager:
    @staticmethod
    def get(file_path: Path, ttl: int) -> Optional[Any]:
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            fetched_at = data.get("fetched_at", 0)
            if time.time() - fetched_at < ttl:
                return data.get("payload")
        except Exception:
            pass
        return None

    @staticmethod
    def set(file_path: Path, payload: Any, extra_meta: Optional[dict] = None) -> None:
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = file_path.with_suffix(".tmp")
            data = {
                "fetched_at": time.time(),
                "payload": payload
            }
            if extra_meta:
                data.update(extra_meta)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f)
            tmp.replace(file_path)
        except Exception:
            pass
