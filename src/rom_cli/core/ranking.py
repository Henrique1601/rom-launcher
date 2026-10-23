"""Módulo de ranking, popularidade (Wikipedia) e orquestração de busca."""

import json
import os
import re
import time
import urllib.parse
from typing import List, Optional, Dict, Any

from rom_cli.config import (
    CACHE_DIR, PLATFORMS, PLATFORM_LABELS, LABELS, BAD_WORDS
)
from rom_cli.core.utils import (
    norm, clean, significant_words, request_http
)
from rom_cli.models import RomItem
from rom_cli.providers import SOURCES, DLA, NPS, DLP, ARCHIVE_ORG, ROMSGAMES

WIKI_LISTS = {
    "switch": "List_of_best-selling_Nintendo_Switch_video_games",
    "ps5": "List_of_best-selling_PlayStation_5_video_games",
    "ps4": "List_of_best-selling_PlayStation_4_video_games",
    "ps3": "List_of_best-selling_PlayStation_3_video_games",
    "ps2": "List_of_best-selling_PlayStation_2_video_games",
    "ps1": "List_of_best-selling_PlayStation_video_games",
    "psp": "List_of_best-selling_PlayStation_Portable_video_games",
    "nds": "List_of_best-selling_Nintendo_DS_video_games",
    "3ds": "List_of_best-selling_Nintendo_3DS_video_games",
    "gba": "List_of_best-selling_Game_Boy_Advance_video_games",
    "gb": "List_of_best-selling_Game_Boy_video_games",
    "snes": "List_of_best-selling_Super_Nintendo_Entertainment_System_video_games",
    "nes": "List_of_best-selling_Nintendo_Entertainment_System_video_games",
    "n64": "List_of_best-selling_Nintendo_64_video_games",
    "gc": "List_of_best-selling_GameCube_video_games",
    "wii": "List_of_best-selling_Wii_video_games",
    "genesis": "List_of_best-selling_Sega_Genesis_games",
    "xbox": "List_of_best-selling_Xbox_video_games",
    "xbox360": "List_of_best-selling_Xbox_360_video_games",
}
POPULAR_FILE = CACHE_DIR / "popular.json"
POPULAR_TTL = 30 * 86400
POPULAR = None
POPULAR_NORM = None
LABEL_KEY = {v: k for k, v in PLATFORM_LABELS.items()}

_WIKI_ATTR = re.compile(r'^[|!]\s*(?:[A-Za-z_:][\w:.-]*\s*=\s*'
                        r'(?:"[^"]*"|\'[^\']*\'|[^\s|]+)\s*)*\|?\s*')
_WIKI_LINK = re.compile(r"\[\[([^\]\|#]+)(?:\|([^\]]+))?\]\]")
_WIKI_SALES = (
    re.compile(r"\{\{nts\|([\d.,]+)\}\}"),
    re.compile(r"\{\{val\|([\d.,]+)"),
    re.compile(r"\b(\d{1,3}(?:,\d{3}){1,}|\d{6,})\b")
)


def _wiki_raw(title: str, depth: int = 0) -> str:
    st, _, body = request_http(
        f"https://en.wikipedia.org/w/index.php?title={title}&action=raw",
        retries=2, timeout=40
    )
    if st != 200 or depth > 2:
        return ""
    text = body.decode("utf-8", "replace")
    m = re.match(r"\s*#REDIRECT\s*\[\[([^\]]+)\]\]", text, re.I)
    if m:
        return _wiki_raw(urllib.parse.quote(m.group(1).replace(" ", "_")), depth + 1)
    return text


def _wiki_tables(text: str) -> List[List[str]]:
    out, cur, depth = [], None, 0
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("{|"):
            if depth == 0:
                cur = []
            depth += 1
        if cur is not None:
            cur.append(line)
        if s.startswith("|}"):
            depth = max(0, depth - 1)
            if depth == 0 and cur is not None:
                out.append(cur)
                cur = None
    return out


def _wiki_rows(lines: List[str]) -> List[str]:
    rows, cur = [], None

    def flush(cells):
        if not cells:
            return
        title, sales = None, 0.0
        for cell in cells:
            body = _WIKI_ATTR.sub("", cell.strip(), count=1)
            if title is None:
                m = _WIKI_LINK.search(body)
                if m:
                    title = re.sub(r"''", "", m.group(2) or m.group(1))
                    title = re.sub(r"&nbsp;|&#160;|\u00a0", " ", title)
                    title = re.sub(r"\s+", " ", title).strip()
            if sales == 0.0:
                for pat in _WIKI_SALES:
                    mm = pat.search(body)
                    if mm:
                        try:
                            sales = float(mm.group(1).replace(",", ""))
                        except ValueError:
                            sales = 0.0
                        if sales:
                            break
        if title and sales > 0:
            rows.append(title)

    for line in lines:
        s = line.strip()
        if s == "|-":
            flush(cur)
            cur = []
        elif cur is not None and s.startswith(("|", "!")):
            cur.append(line)
    flush(cur)
    return rows


def _parse_wiki(text: str) -> List[str]:
    best = []
    for tbl in _wiki_tables(text):
        rows = _wiki_rows(tbl)
        if len(rows) > len(best):
            best = rows
    return best


def load_popular(force: bool = False) -> dict:
    global POPULAR, POPULAR_NORM
    if POPULAR is not None and not force:
        return POPULAR
    if not force and POPULAR_FILE.exists():
        try:
            with open(POPULAR_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            if time.time() - d.get("fetched_at", 0) < POPULAR_TTL and d.get("data"):
                POPULAR = d["data"]
                POPULAR_NORM = None
                return POPULAR
        except Exception:
            pass

    data = {}
    for pk, page in WIKI_LISTS.items():
        try:
            titles = _parse_wiki(_wiki_raw(page))
        except Exception:
            titles = []
        seen, ranked = set(), []
        for t in titles:
            nt = norm(t)
            if nt and nt not in seen:
                seen.add(nt)
                ranked.append(t)
        if ranked:
            data[pk] = ranked

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = POPULAR_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"fetched_at": time.time(), "data": data}, f)
        tmp.replace(POPULAR_FILE)
    except Exception:
        pass

    POPULAR = data
    POPULAR_NORM = None
    return data


def _pop_norm(pk: str) -> dict:
    global POPULAR_NORM
    if POPULAR_NORM is None:
        POPULAR_NORM = {}
    if pk not in POPULAR_NORM:
        POPULAR_NORM[pk] = {norm(t): i for i, t in enumerate((POPULAR or {}).get(pk, []))}
    return POPULAR_NORM[pk]


def pop_rank(pk: str, title: str) -> Optional[int]:
    nt = norm(title)
    if not nt:
        return None
    m = _pop_norm(pk)
    if not m:
        return None
    if nt in m:
        return m[nt]
    best = None
    for wt, i in m.items():
        if nt.startswith(wt + " "):
            if best is None or i < best:
                best = i
    return best


def annotate_popular(results: List[RomItem]) -> List[RomItem]:
    load_popular()
    for r in results:
        pk = (r.extra.get("pk") if r.extra else None) or LABEL_KEY.get(r.platform_label) or r.platform
        if not pk:
            continue
        rk = pop_rank(pk, r.title)
        if rk is not None:
            r.is_star = True
            if r.extra is None:
                r.extra = {}
            r.extra["pop"] = rk
    return results


def rank(results: List[RomItem], query: str) -> List[RomItem]:
    words = significant_words(norm(query).split())

    def score(r: RomItem) -> int:
        t = norm(f"{r.title} {r.platform_label}")
        s = sum(7 for w in words if w in t)
        if words and all(w in t for w in words):
            s += 30
        low = r.title.lower()
        for pat in BAD_WORDS:
            if pat in low:
                s -= 12
        if r.extra and r.extra.get("ext") in ("nsp", "xci"):
            s += 4
        pop = r.extra.get("pop") if r.extra else None
        if pop is not None:
            s += min(12, max(2, 14 - pop))
        if r.kind == "Base":
            s += 3
        elif r.kind in ("Update", "DLC"):
            s -= 3
        if r.source == "archive.org":
            s -= 8
        if r.source == "dlpsgame":
            s -= 5
        if len(r.title) > 70:
            s -= 6
        return s

    return sorted(results, key=score, reverse=True)


def search_all(
    query: str,
    platform_key: Optional[str] = None,
    on_progress=None,
    force: bool = False
) -> List[RomItem]:
    results, seen = [], set()

    def add(batch: List[RomItem]):
        for r in batch:
            key = (r.source, r.title, r.size)
            if key not in seen:
                seen.add(key)
                results.append(r)

    words = significant_words(norm(query).split())
    tries = [query]
    if len(words) >= 2:
        tries.append(" ".join(words))
        tries.append(" ".join(words[:2]))
    tries += sorted(words, key=len, reverse=True)[:2]

    first = True
    for attempt in tries:
        if platform_key:
            src_name, arg = PLATFORMS[platform_key]
            src = SOURCES[src_name]
            if src_name in ("dlarchive", "nps"):
                add(src.search(attempt, arg, on_progress=on_progress, force=force))
            elif src_name == "romsgames":
                add(src.search(attempt, platform_key=platform_key, prefixes=arg))
            else:
                add(src.search(attempt, platform_key=platform_key))
        else:
            try:
                add(ROMSGAMES.search(attempt))
            except Exception:
                pass
            try:
                add(DLA.search(attempt, None, on_progress=on_progress, force=force))
            except Exception:
                pass
            if first:
                try:
                    add(NPS.search(attempt, "ps3", on_progress=on_progress, force=force))
                except Exception:
                    pass
                try:
                    add(DLP.search(attempt, None))
                except Exception:
                    pass
        force = False
        first = False
        if len(results) >= 12:
            break

    if platform_key == "switchports":
        try:
            words = significant_words(norm(query).split())
            for r in ARCHIVE_ORG.port_results(force=force):
                if all(w in norm(r.title) for w in words):
                    add([r])
        except Exception:
            pass
        results = [r for r in results if r.kind == "Port"]
        seen = {(r.source, r.title, r.size) for r in results}

    if platform_key and len(results) < 6 and platform_key in ARCHIVE_ORG.tags:
        try:
            add(ARCHIVE_ORG.search(query, platform_key=platform_key))
        except Exception:
            pass

    if platform_key == "xbox":
        try:
            add(ROMSGAMES.search(query, platform_key="xbox", prefixes=["xbox"]))
        except Exception:
            pass

    annotate_popular(results)
    return results


KIND_ORDER = {"Base": 0, "": 1, "Port": 1, "Update": 2, "DLC": 3}


def browse_items(platform_key: str) -> List[RomItem]:
    if platform_key == "switchports":
        items = DLA.all_items("switch", ports_only=True)
        try:
            items += ARCHIVE_ORG.port_results()
        except Exception:
            pass
        seen, uniq = set(), []
        for r in items:
            k = norm(r.title)
            if k and k not in seen:
                seen.add(k)
                uniq.append(r)
        uniq.sort(key=lambda r: norm(r.title))
        return uniq

    src_name, arg = PLATFORMS[platform_key]
    src = SOURCES[src_name]
    pk = platform_key

    if hasattr(src, "all_items"):
        items = src.all_items(arg)
    else:
        load_popular()
        titles = (POPULAR or {}).get(pk) or []
        if not titles:
            raise RuntimeError(f"{PLATFORM_LABELS.get(pk, pk)}: sem listagem — use a busca")
        items = [
            RomItem(
                title=t,
                platform=pk,
                platform_label=PLATFORM_LABELS.get(pk, pk),
                source="dlpsgame",
                extra={"ext": "pkg", "pk": pk, "pop": i, "search_title": t},
                is_star=True
            )
            for i, t in enumerate(titles)
        ]
        return items

    load_popular()
    if (POPULAR or {}).get(pk):
        def key(r: RomItem):
            kind = KIND_ORDER.get(r.kind, 1)
            size = -int((r.extra or {}).get("bytes") or 0)
            rk = pop_rank(pk, r.title)
            if rk is not None:
                r.is_star = True
                if r.extra is None:
                    r.extra = {}
                r.extra["pop"] = rk
                return (0, rk, kind, size, norm(r.title))
            return (1, 0, kind, size, norm(r.title))
        items.sort(key=key)

    return items
