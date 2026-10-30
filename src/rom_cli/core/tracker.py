"""Rastreador de tempo jogado (Playtime Tracker) e histórico de sessões."""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

from rom_cli.config import CACHE_DIR

TRACKER_FILE = CACHE_DIR / "playtime.json"


class PlaytimeTracker:
    def __init__(self, storage_file: Path = TRACKER_FILE):
        self.storage_file = storage_file
        self.data: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if not self.storage_file.exists():
            return {}
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self) -> None:
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    def record_session(self, game_key: str, duration_seconds: int) -> None:
        """Registra uma sessão concluída de jogo."""
        if duration_seconds < 5:
            # Ignora sessões de menos de 5 segundos (fechamento imediato/teste)
            return

        stats = self.data.get(game_key, {
            "total_seconds": 0,
            "last_played": 0,
            "sessions_count": 0
        })

        stats["total_seconds"] += duration_seconds
        stats["last_played"] = int(time.time())
        stats["sessions_count"] += 1
        self.data[game_key] = stats
        self.save()

    def get_stats(self, game_key: str) -> Dict[str, Any]:
        return self.data.get(game_key, {
            "total_seconds": 0,
            "last_played": 0,
            "sessions_count": 0
        })

    def format_playtime(self, game_key: str) -> str:
        stats = self.get_stats(game_key)
        total = stats.get("total_seconds", 0)
        if total == 0:
            return "Nunca jogado"

        hours = total // 3600
        minutes = (total % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{max(1, minutes)}m"

    def format_last_played(self, game_key: str) -> str:
        stats = self.get_stats(game_key)
        lp = stats.get("last_played", 0)
        if lp == 0:
            return "Nunca"

        diff = time.time() - lp
        if diff < 3600:
            return "Há poucos minutos"
        if diff < 86400:
            hours = int(diff // 3600)
            return f"Hoje (há {hours}h)"
        if diff < 172800:
            return "Ontem"
        days = int(diff // 86400)
        return f"Há {days} dias"


# Instância global do rastreador
TRACKER = PlaytimeTracker()
