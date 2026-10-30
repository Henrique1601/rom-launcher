"""Roleta Gamer: Escolhe aleatoriamente um jogo da biblioteca instalada para jogar."""

import random
from typing import List, Optional
from pathlib import Path

from rom_cli.config import OUT_DIR
from rom_cli.core.launcher import launch_game
from rom_cli.core.tracker import TRACKER
from rom_cli.launcher.scanner import InstalledGame, LibraryScanner


def pick_random_game(
    platform_key: Optional[str] = None,
    prioritize_unplayed: bool = True,
    outdir: Optional[Path] = None
) -> Optional[InstalledGame]:
    """
    Sorteia um jogo da biblioteca instalada.
    Se prioritize_unplayed=True, dá preferência a títulos nunca jogados.
    """
    scanner = LibraryScanner(outdir or OUT_DIR)
    library = scanner.scan_all()

    candidates: List[InstalledGame] = []
    if platform_key:
        candidates = library.get(platform_key, [])
    else:
        for g_list in library.values():
            candidates.extend(g_list)

    if not candidates:
        return None

    if prioritize_unplayed:
        unplayed = [g for g in candidates if TRACKER.get_stats(g.path.stem).get("total_seconds", 0) == 0]
        if unplayed and random.random() < 0.70:  # 70% de chance de sortear um nunca jogado
            return random.choice(unplayed)

    return random.choice(candidates)
