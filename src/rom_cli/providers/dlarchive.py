"""Provedor DlArchive - Switch, NDS, GBA, SNES e PC."""

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple

from rom_cli.config import INDEX_FILE, INDEX_TTL, INDEX_PAGE, CACHE_DIR
from rom_cli.core.utils import (
    request_http, pretty_title, norm, kind_of, platform_of, significant_words
)
from rom_cli.models import RomItem
from rom_cli.providers.base import BaseProvider


class DlArchiveProvider(BaseProvider):
    name = "dlarchive"
    api = "https://uptobox.dlarchive.my.id/files_api.php"
    _cache = None
    _lock = threading.Lock()

    def _entry(self, item: dict) -> dict:
        fn = item.get("filename") or ""
        size = int(item.get("size") or 0)
        return {
            "id": item.get("id"),
            "filename": fn,
            "size": size,
            "folder": item.get("folder") or "",
        }

    def _rehydrate(self, e: dict) -> dict:
        fn = e.get("filename") or ""
        pk, label = platform_of(fn, e.get("folder") or "")
        e["pk"], e["plat"] = pk, label
        e["kind"] = kind_of(fn)
        e["ext"] = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""
        e["title"] = pretty_title(fn)
        e["ntitle"] = norm(e["title"])
        return e

    def _fetch(self, on_progress=None) -> List[dict]:
        st, _, body = request_http(
            f"{self.api}?action=list&limit=1",
            headers={"Accept": "application/json"},
            timeout=60
        )
        total = int(json.loads(body.decode("utf-8", "replace")).get("total") or 0)
        offsets = list(range(0, total, INDEX_PAGE))
        entries, done = [], [0]
        lock = threading.Lock()

        def work(off):
            st, _, body = request_http(
                f"{self.api}?action=list&offset={off}&limit={INDEX_PAGE}",
                headers={"Accept": "application/json"},
                timeout=60,
                retries=4
            )
            items = json.loads(body.decode("utf-8", "replace")).get("items", [])
            with lock:
                for it in items:
                    entries.append(self._entry(it))
                done[0] += 1
                if on_progress:
                    on_progress(done[0], len(offsets))

        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(work, offsets))
        return [self._rehydrate(e) for e in entries]

    def load_index(self, force: bool = False, on_progress=None) -> List[dict]:
        with self._lock:
            if DlArchiveProvider._cache and not force:
                return DlArchiveProvider._cache
            if not force and INDEX_FILE.exists():
                try:
                    with open(INDEX_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if (time.time() - data.get("fetched_at", 0) < INDEX_TTL
                            and data.get("entries")):
                        DlArchiveProvider._cache = [self._rehydrate(e) for e in data["entries"]]
                        return DlArchiveProvider._cache
                except Exception:
                    pass

            entries = self._fetch(on_progress)
            try:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                tmp = INDEX_FILE.with_suffix(".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump({"fetched_at": time.time(), "entries": entries}, f)
                tmp.replace(INDEX_FILE)
            except Exception:
                pass
            DlArchiveProvider._cache = entries
            return entries

    def _to_item(self, e: dict) -> RomItem:
        return RomItem(
            title=e["title"],
            platform=e["pk"],
            platform_label=e["plat"],
            source=self.name,
            url=f"{self.api}?action=file-url&id={e['id']}",
            size=e["size"],
            kind=e["kind"],
            extra={
                "id": e["id"],
                "filename": e["filename"],
                "ext": e["ext"],
                "pk": e["pk"],
                "bytes": e["size"],
            }
        )

    def search(
        self,
        query: str,
        platform_key: Optional[str] = None,
        on_progress=None,
        force: bool = False
    ) -> List[RomItem]:
        idx = self.load_index(force=force, on_progress=on_progress)
        toks = significant_words(norm(query).split())
        out = []
        for e in idx:
            if platform_key and e["pk"] != platform_key:
                continue
            nt = e["ntitle"]
            hits = sum(1 for t in toks if t in nt)
            if hits == 0:
                continue
            if platform_key is None and hits < len(toks):
                continue
            out.append((hits, e))
        if not out and toks:
            for e in idx:
                if platform_key and e["pk"] != platform_key:
                    continue
                if toks[0] in e["ntitle"]:
                    out.append((1, e))
        out.sort(key=lambda x: (-x[0], len(x[1]["title"])))
        return [self._to_item(e) for _hits, e in out[:120]]

    def all_items(self, pk: Optional[str] = None, ports_only: bool = False) -> List[RomItem]:
        out = []
        for e in self.load_index():
            if not e["pk"] or (pk and e["pk"] != pk):
                continue
            if ports_only and e.get("kind") != "Port":
                continue
            out.append(self._to_item(e))
        out.sort(key=lambda r: norm(r.title))
        return out

    def resolve(self, item: RomItem) -> Tuple[str, str]:
        fid = item.extra.get("id") if item.extra else None
        st, _, body = request_http(
            f"{self.api}?action=file-url&id={fid}",
            headers={"Accept": "application/json"},
            timeout=60,
            retries=3
        )
        if st != 200:
            raise RuntimeError(f"servidor respondeu {st}")
        data = json.loads(body.decode("utf-8", "replace"))
        if not data.get("ok") or not data.get("url"):
            raise RuntimeError(data.get("error") or "link indisponível")
        return data["url"], (item.extra.get("filename") if item.extra else None) or item.title
