"""Provedor Archive.org - Ports de Switch e Fallback de consoles clássicos."""

import json
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple

from rom_cli.config import CACHE_DIR, PLATFORM_LABELS
from rom_cli.core.utils import request_http, clean, pretty_title, norm
from rom_cli.models import RomItem
from rom_cli.providers.base import BaseProvider


class ArchiveOrgProvider(BaseProvider):
    name = "archive.org"
    base = "https://archive.org"
    tags = {
        "nes": ("NES", ["nes", "zip"]),
        "snes": ("SNES", ["sfc", "smc", "zip"]),
        "n64": ("Nintendo 64", ["z64", "n64", "v64", "zip"]),
        "gb": ("Game Boy", ["gb", "zip"]),
        "gbc": ("Game Boy Color", ["gbc", "zip"]),
        "gba": ("Game Boy Advance", ["gba", "zip"]),
        "nds": ("Nintendo DS", ["nds", "zip"]),
        "3ds": ("Nintendo 3DS", ["cia", "3ds", "zip"]),
        "gc": ("GameCube", ["iso", "gcm", "zip"]),
        "wii": ("Wii", ["iso", "wbfs", "zip"]),
        "ps1": ("PlayStation", ["bin", "cue", "iso", "zip"]),
        "ps2": ("PlayStation 2", ["iso", "zip"]),
        "ps3": ("PlayStation 3", ["iso", "pkg", "zip"]),
        "psp": ("PlayStation Portable", ["iso", "cso", "pbp", "zip"]),
        "genesis": ("Genesis", ["md", "bin", "gen", "zip"]),
        "mastersystem": ("Master System", ["sms", "zip"]),
        "dreamcast": ("Dreamcast", ["cdi", "gdi", "chd", "zip"]),
        "saturn": ("Saturn", ["cue", "bin", "chd", "zip"]),
        "arcade": ("Arcade", ["zip"]),
    }
    skip = ("_files.xml", "_meta.xml", "_meta.sqlite", "_archive.torrent", ".torrent")
    port_queries = (
        'title:("switch port") AND mediatype:software',
        'title:("homebrew port") AND mediatype:software',
        'title:(nsp) AND (port OR homebrew) AND mediatype:software',
        'title:("nintendo switch") AND (port OR homebrew) AND mediatype:software',
    )
    port_exts = ["nsp", "xci", "nsz", "zip", "7z", "rar"]

    ports_file = CACHE_DIR / "switchports.json"
    ports_ttl = 7 * 86400
    ports_ver = 2
    _ports_cache = None

    def switch_ports(self, force: bool = False, on_progress=None) -> List[dict]:
        if self._ports_cache is not None and not force:
            return self._ports_cache
        if not force and self.ports_file.exists():
            try:
                with open(self.ports_file, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if (time.time() - d.get("fetched_at", 0) < self.ports_ttl
                        and d.get("ver") == self.ports_ver and d.get("items")):
                    self._ports_cache = d["items"]
                    return self._ports_cache
            except Exception:
                pass

        pair, seen = [], set()
        for q in self.port_queries:
            url = (f"{self.base}/advancedsearch.php?q={urllib.parse.quote(q)}"
                   "&fl%5B%5D=identifier&fl%5B%5D=title&rows=60&output=json")
            st, _, body = request_http(url, retries=2)
            if st != 200:
                continue
            try:
                docs = json.loads(body.decode("utf-8", "replace"))["response"]["docs"]
            except Exception:
                continue
            for doc in docs:
                ident = doc.get("identifier")
                if ident and ident not in seen:
                    seen.add(ident)
                    pair.append((ident, clean(doc.get("title") or "")))

        out, state = [], {"done": 0}

        def work(item):
            ident, title = item
            try:
                st, _, body = request_http(
                    f"{self.base}/metadata/{ident}", retries=2,
                    headers={"Accept": "application/json"}, timeout=40
                )
                data = json.loads(body.decode("utf-8", "replace")) if st == 200 else {}
            except Exception:
                data = {}
            state["done"] += 1
            if on_progress:
                on_progress(state["done"], len(pair))
            files = [f for f in data.get("files", []) if not f["name"].endswith(self.skip)]
            for ext in self.port_exts:
                cands = [f for f in files if f["name"].lower().endswith("." + ext)]
                if cands:
                    best = max(cands, key=lambda f: int(f.get("size") or 0))
                    return {
                        "title": title or pretty_title(best["name"]),
                        "ident": ident,
                        "size": int(best.get("size") or 0),
                        "file": best["name"],
                        "nsp": ext in ("nsp", "xci", "nsz")
                    }
            return None

        with ThreadPoolExecutor(max_workers=6) as pool:
            for r in pool.map(work, pair):
                if r:
                    out.append(r)

        block = (
            "theme", "dbi", "installer", "autoloader", "payload", "firmware",
            "devkitpro", "source code", "godot", "psvita", "ps vita", " vita",
            "3ds", "psp", "wiiu", "wii u"
        )
        out = [r for r in out if not any(b in r["title"].lower() for b in block)]
        out.sort(key=lambda x: (not x.get("nsp"), norm(x["title"])))

        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            tmp = self.ports_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"fetched_at": time.time(), "ver": self.ports_ver, "items": out}, f)
            tmp.replace(self.ports_file)
        except Exception:
            pass

        self._ports_cache = out
        return out

    def port_results(self, force: bool = False, on_progress=None) -> List[RomItem]:
        out = []
        for it in self.switch_ports(force=force, on_progress=on_progress):
            out.append(RomItem(
                title=it["title"],
                platform="switch",
                platform_label=PLATFORM_LABELS["switch"],
                source=self.name,
                url=f"{self.base}/details/{it['ident']}",
                size=it["size"],
                kind="Port",
                extra={
                    "exts": self.port_exts,
                    "ext": "nsp",
                    "pk": "switch",
                    "kind": "Port"
                }
            ))
        return out

    def search(
        self,
        query: str,
        platform_key: Optional[str] = None,
        on_progress=None,
        force: bool = False
    ) -> List[RomItem]:
        if platform_key not in self.tags:
            return []
        tag, exts = self.tags[platform_key]
        q = f'title:({query}) AND mediatype:software AND ({tag})'
        url = (f"{self.base}/advancedsearch.php?q={urllib.parse.quote(q)}"
               "&fl%5B%5D=identifier&fl%5B%5D=title&rows=20&page=1&output=json")
        st, _, body = request_http(url, retries=2)
        if st != 200:
            return []
        try:
            docs = json.loads(body.decode("utf-8", "replace"))["response"]["docs"]
        except Exception:
            return []
        out = []
        for doc in docs:
            title = clean(doc.get("title") or "")
            if title:
                label = PLATFORM_LABELS.get(platform_key, platform_key)
                out.append(RomItem(
                    title=title,
                    platform=platform_key,
                    platform_label=label,
                    source=self.name,
                    url=f"{self.base}/details/{doc['identifier']}",
                    extra={"exts": exts}
                ))
        return out

    def resolve(self, item: RomItem) -> Tuple[str, str]:
        ident = item.url.rsplit("/", 1)[-1]
        st, _, body = request_http(
            f"{self.base}/metadata/{ident}", retries=2,
            headers={"Accept": "application/json"}
        )
        if st != 200:
            raise RuntimeError(f"item indisponível ({st})")
        data = json.loads(body.decode("utf-8", "replace"))
        files = [f for f in data.get("files", []) if not f["name"].endswith(self.skip)]
        if not files:
            raise RuntimeError("item sem arquivo baixável")

        exts = item.extra.get("exts", []) if item.extra else []
        for ext in exts:
            matches = [f for f in files if f["name"].lower().endswith("." + ext)]
            if matches:
                best = max(matches, key=lambda f: int(f.get("size") or 0))
                return (f"{self.base}/download/{ident}/{urllib.parse.quote(best['name'])}",
                        best["name"])

        loose = [f for f in files if re.search(
            r"\.(zip|7z|rar|ips|bps|xdelta|iso|bin|cue|chd|cia|3ds|nsp|xci)$", f["name"], re.I)]
        if loose:
            best = max(loose, key=lambda f: int(f.get("size") or 0))
            return f"{self.base}/download/{ident}/{urllib.parse.quote(best['name'])}", best["name"]

        raise RuntimeError("nenhum formato compatível no item")
