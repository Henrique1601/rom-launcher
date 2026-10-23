"""Utilitários gerais para manipulação de strings, requisições HTTP e formatação."""

import html as htmllib
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from typing import List, Tuple, Optional, Dict, Any

from rom_cli.config import UA, STOP_WORDS, ROM_EXTS, PLATFORM_LABELS

TTY = sys.stdout.isatty()
EXT_RE = re.compile(r"\.(" + "|".join(ROM_EXTS) + r")$", re.I)


def write(text: str = "", newline: bool = True) -> None:
    sys.stdout.write(text)
    if newline and not text.endswith("\n"):
        sys.stdout.write("\n")
    sys.stdout.flush()


def status(msg: str) -> None:
    if TTY:
        write(f"\r\033[K  {msg}")
    else:
        write(f"  {msg}\n")


def clear_status() -> None:
    if TTY:
        write("\r\033[K")


def human_size(n: Optional[float]) -> str:
    if not n:
        return "?"
    n = float(n)
    for unit in ("B", "kB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def norm(s: Optional[str]) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def clean(s: Optional[str]) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = htmllib.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def significant_words(words: List[str]) -> List[str]:
    sig = [w for w in words if w not in STOP_WORDS and len(w) > 1]
    return sig or words


def pretty_title(fn: Optional[str]) -> str:
    base = EXT_RE.sub("", fn or "")
    base = re.sub(r"\[[^\]]*\]", " ", base)
    base = re.sub(r"\bv\d+(?:\.\d+)*\b", " ", base, flags=re.I)
    base = base.replace("_", " ")
    base = re.sub(r"^\s*download\s+", "", base, flags=re.I)
    base = re.sub(r"\s+", " ", base).strip(" .-")
    return base or (fn or "")


def kind_of(fn: Optional[str]) -> str:
    low = (fn or "").lower()
    if re.search(r"\bports?\b", low) or "homebrew" in low:
        return "Port"
    if "[dlc" in low or " dlc" in low or "dlc " in low:
        return "DLC"
    if "[up " in low or "upd" in low or "update" in low or re.search(r"\bv\d+", low):
        return "Update"
    if "[base]" in low:
        return "Base"
    return ""


def platform_of(fn: Optional[str], folder: Optional[str]) -> Tuple[str, str]:
    ext = fn.rsplit(".", 1)[-1].lower() if fn and "." in fn else ""
    low = (fn or "").lower()
    flat = re.sub(r"[_\-]+", " ", low)
    if (ext in ("nsp", "xci", "nsz") or re.search(r"\b(?:nintendo )?switch\b", flat)
            or re.search(r"\b01[0-9a-f]{12}\b", low) or kind_of(fn) == "Port"):
        return "switch", "Switch"
    fl = (folder or "").lower()
    for token, key in (("nintendo_ds", "nds"), ("gameboy_advance", "gba"),
                       ("super_nintendo", "snes"), ("playstation_2", "ps2"),
                       ("playstation_portable", "psp"), ("game_pc", "pc"),
                       ("gameboy_color", "gbc"), ("gameboy", "gb"), ("sega", "genesis")):
        if token in fl:
            return key, PLATFORM_LABELS.get(key, key.upper())
    return "", "Other"


def safe_name(name: str, fallback: str, ext: str) -> str:
    base = clean(name) or fallback
    base = EXT_RE.sub("", base)
    base = re.sub(r'[\\/:*?"<>|]', " ", base)
    base = re.sub(r"\s+", " ", base).strip(" .")[:140] or fallback
    return f"{base}{ext}"


def request_http(
    url: str,
    data: Optional[bytes] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 40,
    retries: int = 3,
    method: Optional[str] = None
) -> Tuple[int, Any, bytes]:
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("User-Agent", UA)
        req.add_header("Accept-Language", "en-US,en;q=0.9,pt-BR;q=0.8")
        req.add_header("Accept", "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.build_opener().open(req, timeout=timeout) as r:
                return r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504) and attempt + 1 < retries:
                time.sleep(1 + attempt)
                continue
            return e.code, e.headers, e.read()
        except Exception as e:
            last = e
            if attempt + 1 < retries:
                time.sleep(1 + attempt)
    raise last
