"""Integração com o RetroAchievements (Conquistas e Troféus para jogos clássicos)."""

import json
import re
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional

from rom_cli.config import CACHE_DIR
from rom_cli.core.utils import request_http, norm, clean

RA_CACHE_DIR = CACHE_DIR / "retroachievements"
RA_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Mapeamento de consoles para IDs do RetroAchievements
RA_CONSOLE_IDS = {
    "genesis": 1,
    "n64": 2,
    "snes": 3,
    "gb": 4,
    "gba": 5,
    "gbc": 6,
    "nes": 7,
    "ps1": 12,
    "ps2": 21,
    "psp": 41,
    "saturn": 29,
    "dreamcast": 40,
    "arcade": 27,
    "mastersystem": 11,
    "nds": 18
}


class RetroAchievementsClient:
    def __init__(self, cache_dir: Path = RA_CACHE_DIR):
        self.cache_dir = cache_dir

    def get_game_info(self, title: str, platform_key: str) -> Optional[Dict[str, Any]]:
        """
        Busca metadados de conquistas e pontuação do jogo no RetroAchievements.
        Retorna informações sobre total de conquistas e pontos disponíveis.
        """
        console_id = RA_CONSOLE_IDS.get(platform_key)
        if not console_id:
            return None

        safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)[:70]
        cache_file = self.cache_dir / f"{platform_key}_{safe_title}.json"

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # Limpa o título (remove tags de região e versão)
        clean_name = re.sub(r"\[.*?\]", "", title)
        clean_name = re.sub(r"\(.*?\)", "", clean_name).strip()
        encoded = urllib.parse.quote(clean_name)

        # Consulta busca pública no RetroAchievements
        url = f"https://retroachievements.org/dorequest.php?r=search&s={encoded}"

        try:
            status, _, body = request_http(url, timeout=10, retries=1)
            if status != 200 or not body:
                return None

            data = json.loads(body.decode("utf-8", "replace"))
            results = data.get("Results", [])

            # Filtra resultados correspondentes ao console correto
            matched_game = None
            for item in results:
                if item.get("ConsoleID") == console_id:
                    matched_game = item
                    break

            if not matched_game and results:
                # Fallback para o primeiro jogo encontrado caso console seja similar
                matched_game = results[0]

            if not matched_game:
                return None

            info = {
                "game_id": matched_game.get("ID"),
                "title": matched_game.get("Title", clean_name),
                "achievements_count": int(matched_game.get("NumAchievements") or 0),
                "points": int(matched_game.get("Points") or 0),
                "badge_url": f"https://retroachievements.org{matched_game.get('ImageIcon')}" if matched_game.get("ImageIcon") else None,
                "console": matched_game.get("ConsoleName", platform_key.upper()),
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(info, f, indent=2)

            return info
        except Exception:
            return None


RA_CLIENT = RetroAchievementsClient()
