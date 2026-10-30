"""Provedor Myrient - Acervo No-Intro e Redump preservado."""

import html as htmllib
import re
import urllib.parse
from typing import List, Optional, Tuple

from rom_cli.config import PLATFORM_LABELS
from rom_cli.core.utils import request_http, clean, norm, significant_words
from rom_cli.models import RomItem
from rom_cli.providers.base import BaseProvider


class MyrientProvider(BaseProvider):
    name = "myrient"
    base = "https://myrient.erista.me/files/"

    # Mapeamento de coleções No-Intro e Redump no Myrient
    COLLECTIONS = {
        "snes": ("No-Intro/Nintendo - Super Nintendo Entertainment System/", ".zip"),
        "nes": ("No-Intro/Nintendo - Nintendo Entertainment System/", ".zip"),
        "gba": ("No-Intro/Nintendo - Game Boy Advance/", ".zip"),
        "gbc": ("No-Intro/Nintendo - Game Boy Color/", ".zip"),
        "gb": ("No-Intro/Nintendo - Game Boy/", ".zip"),
        "nds": ("No-Intro/Nintendo - Nintendo DS (Decrypted)/", ".zip"),
        "n64": ("No-Intro/Nintendo - Nintendo 64 (BigEndian)/", ".zip"),
        "genesis": ("No-Intro/Sega - Mega Drive - Genesis/", ".zip"),
        "mastersystem": ("No-Intro/Sega - Master System - Mark III/", ".zip"),
        "gamecube": ("Redump/Nintendo - GameCube - NTSC-U/", ".zip"),
        "ps1": ("Redump/Sony - PlayStation - NTSC-U/", ".zip"),
        "ps2": ("Redump/Sony - PlayStation 2 - NTSC-U/", ".zip"),
        "psp": ("Redump/Sony - PlayStation Portable/", ".zip"),
        "xbox": ("Redump/Microsoft - Xbox/", ".zip"),
    }

    _index_cache = {}

    def _get_directory_listing(self, path: str) -> List[Tuple[str, str]]:
        """Lê a listagem HTML do diretório do Myrient e retorna tuplas (nome_arquivo, href)."""
        if path in self._index_cache:
            return self._index_cache[path]

        url = f"{self.base}{path}"
        try:
            st, _, body = request_http(url, timeout=30, retries=2)
            if st != 200:
                return []
            content = body.decode("utf-8", "replace")
            # Extrai links <a href="...">filename</a>
            matches = re.findall(r'<a\s+href="([^"]+)">([^<]+)</a>', content)
            items = []
            for href, name in matches:
                name = htmllib.unescape(name.strip())
                if name in ("../", "Parent Directory") or href.startswith("?"):
                    continue
                items.append((name, urllib.parse.urljoin(url, href)))
            self._index_cache[path] = items
            return items
        except Exception:
            return []

    def search(
        self,
        query: str,
        platform_key: Optional[str] = None,
        on_progress=None,
        force: bool = False
    ) -> List[RomItem]:
        if not platform_key or platform_key not in self.COLLECTIONS:
            return []

        folder, default_ext = self.COLLECTIONS[platform_key]
        items = self._get_directory_listing(folder)
        if not items:
            return []

        toks = significant_words(norm(query).split())
        out = []

        for name, link in items:
            nt = norm(name)
            hits = sum(1 for t in toks if t in nt)
            if hits > 0:
                out.append((hits, name, link))

        out.sort(key=lambda x: (-x[0], len(x[1])))
        label = PLATFORM_LABELS.get(platform_key, platform_key)

        results = []
        for _hits, name, link in out[:40]:
            clean_title = re.sub(r"\.[a-zA-Z0-9]+$", "", name)
            results.append(RomItem(
                title=clean_title,
                platform=platform_key,
                platform_label=label,
                source=self.name,
                url=link,
                extra={"filename": name, "ext": name.rsplit(".", 1)[-1].lower() if "." in name else "zip"}
            ))

        return results

    def resolve(self, item: RomItem) -> Tuple[str, str]:
        filename = item.extra.get("filename") if item.extra else None
        return item.url, filename or f"{item.title}.zip"
