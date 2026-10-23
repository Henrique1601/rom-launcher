"""Provedor NoPayStation - PS3, PS Vita, PSP e PSX direto do CDN da Sony."""

import json
import re
import threading
import time
from typing import List, Optional, Tuple

from rom_cli.config import CACHE_DIR, PLATFORM_LABELS
from rom_cli.core.utils import request_http, pretty_title, norm, significant_words
from rom_cli.models import RomItem
from rom_cli.providers.base import BaseProvider


class NoPayStationProvider(BaseProvider):
    name = "nps"
    base = "https://nopaystation.com/tsv/"
    tsv = {
        "ps3": "PS3_GAMES.tsv",
        "psv": "PSV_GAMES.tsv",
        "psp": "PSP_GAMES.tsv",
        "ps1": "PSX_GAMES.tsv"
    }
    cache_file = CACHE_DIR / "nps.json"
    _cache = None
    _lock = threading.Lock()

    def _fetch(self, key: str) -> List[dict]:
        st, _, body = request_http(self.base + self.tsv[key], timeout=120, retries=3)
        if st != 200:
            return []
        lines = body.decode("utf-8", "replace").splitlines()
        if not lines:
            return []
        hdr = [h.strip().lower() for h in lines[0].split("\t")]
        i_size = next((i for i, n in enumerate(hdr) if "size" in n), None)
        i_orig = next((i for i, n in enumerate(hdr) if "original name" in n), None)
        rows = []
        for line in lines[1:]:
            c = line.split("\t")
            url = next((x for x in c if x.startswith("http")), None)
            if not url or len(c) < 3:
                continue
            size = 0
            if i_size is not None and i_size < len(c):
                digits = re.sub(r"[^0-9]", "", c[i_size])
                size = int(digits) if digits else 0
            orig = c[i_orig] if i_orig is not None and i_orig < len(c) else ""
            rows.append({
                "tid": c[0],
                "region": c[1] if len(c) > 1 else "",
                "name": c[2],
                "url": url,
                "size": size,
                "orig": orig
            })
        return rows

    def load(self, force: bool = False, on_progress=None) -> dict:
        with self._lock:
            if NoPayStationProvider._cache and not force:
                return NoPayStationProvider._cache
            if not force and self.cache_file.exists():
                try:
                    with open(self.cache_file, "r", encoding="utf-8") as f:
                        d = json.load(f)
                    if time.time() - d.get("fetched_at", 0) < 7 * 86400 and d.get("data"):
                        NoPayStationProvider._cache = d["data"]
                        return NoPayStationProvider._cache
                except Exception:
                    pass

            data = {}
            for i, k in enumerate(self.tsv, 1):
                if on_progress:
                    on_progress(i, len(self.tsv))
                data[k] = self._fetch(k)
            try:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                tmp = self.cache_file.with_suffix(".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump({"fetched_at": time.time(), "data": data}, f)
                tmp.replace(self.cache_file)
            except Exception:
                pass
            NoPayStationProvider._cache = data
            return data

    def _to_item(self, e: dict, pk: str) -> RomItem:
        title = pretty_title(e["name"])
        label = PLATFORM_LABELS.get(pk, "PS3")
        return RomItem(
            title=title,
            platform=pk,
            platform_label=label,
            source=self.name,
            url=e["url"],
            size=e["size"],
            extra={
                "ext": "pkg",
                "bytes": e["size"],
                "tid": e["tid"],
                "pk": pk,
                "filename": f"{title} [{e['tid']}].pkg"
            }
        )

    def search(
        self,
        query: str,
        platform_key: Optional[str] = None,
        on_progress=None,
        force: bool = False
    ) -> List[RomItem]:
        pk = platform_key or "ps3"
        rows = self.load(force=force, on_progress=on_progress).get(pk, [])
        toks = significant_words(norm(query).split())
        scored = []
        for e in rows:
            nt = norm(f"{e['name']} {e['orig']}")
            hits = sum(1 for t in toks if t in nt)
            if hits:
                scored.append((hits, e))
        scored.sort(key=lambda x: (-x[0], len(x[1]["name"])))
        return [self._to_item(e, pk) for _hits, e in scored[:80]]

    def all_items(self, pk: Optional[str] = None) -> List[RomItem]:
        platform = pk or "ps3"
        rows = self.load().get(platform, [])
        out = [self._to_item(e, platform) for e in rows]
        out.sort(key=lambda r: norm(r.title))
        return out

    def resolve(self, item: RomItem) -> Tuple[str, str]:
        filename = item.extra.get("filename") if item.extra else None
        return item.url, filename or item.title
