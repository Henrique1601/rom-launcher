"""Scanner recursivo de ROMs e jogos instalados localmente na biblioteca."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from rom_cli.config import OUT_DIR, PLATFORM_LABELS, ROM_EXTS


@dataclass
class InstalledGame:
    title: str
    path: Path
    platform_key: str
    platform_label: str
    size: int
    extension: str


class LibraryScanner:
    def __init__(self, base_dir: Path = OUT_DIR):
        self.base_dir = Path(base_dir)

    def scan_all(self) -> Dict[str, List[InstalledGame]]:
        """
        Escaneia o diretório de ROMs e organiza os jogos encontrados por plataforma.
        Retorna: {platform_key: [InstalledGame, ...]}
        """
        library: Dict[str, List[InstalledGame]] = {}

        if not self.base_dir.exists():
            return library

        # Mapeia rótulos de pastas para chaves de plataforma
        label_to_key = {label.lower(): key for key, label in PLATFORM_LABELS.items()}
        for k in PLATFORM_LABELS:
            label_to_key[k.lower()] = k

        for item in self.base_dir.iterdir():
            if item.is_dir():
                folder_name = item.name.lower()
                pk = label_to_key.get(folder_name, folder_name)
                games = self._scan_platform_folder(item, pk)
                if games:
                    library[pk] = games
            elif item.is_file():
                ext = item.suffix.lstrip(".").lower()
                if ext in ROM_EXTS:
                    # Jogo na raiz da pasta de roms
                    game = InstalledGame(
                        title=item.stem,
                        path=item,
                        platform_key="other",
                        platform_label="Outros",
                        size=item.stat().st_size,
                        extension=ext
                    )
                    library.setdefault("other", []).append(game)

        return library

    def _scan_platform_folder(self, folder: Path, platform_key: str) -> List[InstalledGame]:
        games = []
        label = PLATFORM_LABELS.get(platform_key, platform_key.upper())

        for file_path in folder.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lstrip(".").lower()
                if ext in ROM_EXTS:
                    # Ignora arquivos parciais de download
                    if file_path.name.endswith(".part"):
                        continue
                    games.append(InstalledGame(
                        title=file_path.stem,
                        path=file_path,
                        platform_key=platform_key,
                        platform_label=label,
                        size=file_path.stat().st_size,
                        extension=ext
                    ))

        games.sort(key=lambda g: g.title.lower())
        return games

    def find_game(self, query: str, platform_key: Optional[str] = None) -> List[InstalledGame]:
        """Busca um jogo local pelo nome na biblioteca."""
        library = self.scan_all()
        q = query.lower()
        matches = []

        for pk, games in library.items():
            if platform_key and pk != platform_key:
                continue
            for g in games:
                if q in g.title.lower():
                    matches.append(g)

        return matches
