"""Provedor DlpsGame - PS4 e PS5 via WP REST API."""

import html as htmllib
import json
import os
import re
import urllib.parse
from typing import List, Optional, Tuple

from rom_cli.config import PLATFORM_LABELS
from rom_cli.core.utils import request_http, clean
from rom_cli.models import RomItem
from rom_cli.providers.base import BaseProvider


class DlpsGameProvider(BaseProvider):
    name = "dlpsgame"
    base = "https://dlpsgame.com"
    HOSTS = (
        "drive.google.com", "docs.google.com", "mediafire.com", "1fichier.com",
        "gofile.io", "akirabox", "vikingfile", "rootz.so", "1cloudfile.com",
        "ranoz.gg", "mega.nz"
    )

    def search(
        self,
        query: str,
        platform_key: Optional[str] = None,
        on_progress=None,
        force: bool = False
    ) -> List[RomItem]:
        url = (f"{self.base}/wp-json/wp/v2/search?"
               f"search={urllib.parse.quote_plus(query)}&per_page=20")
        st, _, body = request_http(url, headers={"Accept": "application/json"}, retries=2)
        if st != 200:
            return []
        try:
            data = json.loads(body.decode("utf-8", "replace"))
        except Exception:
            return []

        out = []
        for x in data:
            link = x.get("url") or ""
            slug = link.rstrip("/").rsplit("/", 1)[-1].lower()
            key = "ps5" if "ps5" in slug else "ps4" if "ps4" in slug else "ps3" if "ps3" in slug else None
            if not key or (platform_key and key != platform_key):
                continue
            title = clean(x.get("title") or "")
            if title:
                out.append(RomItem(
                    title=title,
                    platform=key,
                    platform_label=PLATFORM_LABELS.get(key, key.upper()),
                    source=self.name,
                    url=link,
                    extra={"ext": "pkg", "pk": key}
                ))
        return out

    def links(self, page_url: str) -> List[str]:
        st, _, body = request_http(page_url, retries=2)
        if st != 200:
            return []
        h = body.decode("utf-8", "replace")
        urls = []
        for u in re.findall(r'href="(https?://[^"]+)"', h):
            u = htmllib.unescape(u)
            if any(x in u for x in self.HOSTS) and u not in urls:
                urls.append(u)
        return urls

    def resolve(self, item: RomItem) -> Tuple[str, str]:
        page_url = item.url
        links = item.extra.get("links") if item.extra else None
        if not links:
            links = self.links(page_url)
        if not links:
            raise RuntimeError(f"sem links no post — abra {page_url}")

        order = []
        for host in ("mediafire", "google", "1fichier", "gofile", "akirabox",
                     "vikingfile", "rootz", "1cloudfile", "ranoz", "mega"):
            order += [u for u in links if host in u and u not in order]
        order += [u for u in links if u not in order]

        errors = []
        for u in order:
            try:
                if "mediafire.com" in u:
                    d, n = self._mediafire(u)
                    return d, n
                if "google.com" in u:
                    return self._gdrive(u), ""
                if "1fichier.com" in u:
                    d = self._1fichier(u)
                    if d:
                        return d, urllib.parse.unquote(os.path.basename(
                            urllib.parse.urlparse(d).path)) or ""
                    errors.append("1fichier sem vaga grátis")
            except Exception as e:
                errors.append(f"{u.split('/')[2]}: {e}")

        raise RuntimeError("download direto indisponível (" + "; ".join(errors or ["host JS"])
                           + ") — links: " + " ".join(order[:4]))

    def _mediafire(self, u: str) -> Tuple[str, str]:
        m = re.search(r"/file/[^/]+/([^/]+)", u)
        name = urllib.parse.unquote(m.group(1)) if m else ""
        st, _, body = request_http(u, retries=2)
        d = re.search(r'href="(https://download[^"]+\.mediafire\.com/[^"]+)"',
                      body.decode("utf-8", "replace"))
        if not d:
            raise RuntimeError("link mediafire não encontrado")
        return d.group(1), name

    def _gdrive(self, u: str) -> str:
        m = re.search(r"/(?:file/d/|id=)([A-Za-z0-9_-]{20,})", u)
        if not m:
            raise RuntimeError("id do drive não encontrado")
        return (f"https://drive.usercontent.google.com/download?id={m.group(1)}"
                "&export=download&confirm=t")

    def _1fichier(self, u: str) -> Optional[str]:
        st, _, body = request_http(u, retries=2)
        h = body.decode("utf-8", "replace")
        m = re.search(r'href="(https?://[a-z0-9]+\.1fichier\.com/[^"]+)"[^>]*class="ok"', h)
        if m:
            return htmllib.unescape(m.group(1))
        st, _, body = request_http(
            u, data=b"ad=1", retries=2,
            headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": u}
        )
        h = body.decode("utf-8", "replace")
        m = re.search(r'(https?://[a-z0-9]+\.1fichier\.com/[^"\']+\.(?:pkg|zip|rar|7z|iso|part\d+|bin))', h)
        return htmllib.unescape(m.group(1)) if m else None
