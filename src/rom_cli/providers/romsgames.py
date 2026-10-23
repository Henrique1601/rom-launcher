"""Provedor RomsGames - PS1, PS2, PSP, Retro Nintendo e Sega."""

import json
import re
import urllib.parse
from typing import List, Optional, Tuple

from rom_cli.config import LABELS
from rom_cli.core.utils import request_http, clean
from rom_cli.models import RomItem
from rom_cli.providers.base import BaseProvider

PLATFORM_RE = re.compile(r"^/([a-z0-9\-]+?)-rom-")


class RomsGamesProvider(BaseProvider):
    name = "romsgames"
    base = "https://www.romsgames.net"

    def search(
        self,
        query: str,
        platform_key: Optional[str] = None,
        prefixes: Optional[List[str]] = None,
        on_progress=None,
        force: bool = False
    ) -> List[RomItem]:
        url = f"{self.base}/search/hint/?q={urllib.parse.quote_plus(query)}"
        st, _, body = request_http(
            url,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json"
            },
            retries=2
        )
        if st != 200:
            return []
        try:
            data = json.loads(body.decode("utf-8", "replace"))
        except Exception:
            return []

        out, seen = [], set()
        for item in data:
            href = item.get("url") or ""
            pm = PLATFORM_RE.match(href)
            if not pm:
                continue
            prefix = pm.group(1)
            if prefixes and prefix not in prefixes:
                continue
            if href in seen:
                continue
            seen.add(href)
            title = clean(item.get("name") or "")
            if not title:
                continue
            label = LABELS.get(prefix, prefix.replace("-", " ").title())
            out.append(RomItem(
                title=title,
                platform=prefix,
                platform_label=label,
                source=self.name,
                url=self.base + href,
                extra={"ext": "zip", "href": href}
            ))
        return out

    def resolve(self, item: RomItem) -> Tuple[str, str]:
        page_url = item.url
        st, _, body = request_http(page_url, retries=2)
        if st != 200:
            raise RuntimeError(f"página indisponível ({st})")
        page = body.decode("utf-8", "replace")
        action = re.search(r'<form[^>]*id="download-form"[^>]*action="([^"]+)"', page)
        media = re.search(r'data-media-id="(\d+)"', page)
        if not action or not media:
            raise RuntimeError("botão de download não encontrado")
        form = urllib.parse.urljoin(self.base, action.group(1))
        st, _, body = request_http(
            form + "?download",
            data=f"mediaId={media.group(1)}&g-recaptcha-response=".encode(),
            headers={
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": page_url
            },
            retries=3
        )
        if st != 200:
            raise RuntimeError(f"servidor de download respondeu {st}")
        try:
            data = json.loads(body.decode("utf-8", "replace"))
        except Exception:
            raise RuntimeError("resposta de download inválida")
        url = data.get("downloadUrl")
        if not url:
            raise RuntimeError("link de download ausente")
        return url, urllib.parse.unquote(data.get("downloadName") or "")
