"""Motor de download com suporte a HTTP Range (retomada) e barra de progresso."""

import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Optional, Tuple, Union

from rom_cli.config import UA
from rom_cli.core.utils import human_size, safe_name
from rom_cli.core.validator import validate_file, fix_magic_extension
from rom_cli.models import RomItem


def stream_download(
    url: str,
    dest_path: Path,
    referer: Optional[str] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> int:
    part_path = dest_path.with_suffix(dest_path.suffix + ".part")
    pos = part_path.stat().st_size if part_path.exists() else 0

    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    if referer:
        req.add_header("Referer", referer)
    if pos:
        req.add_header("Range", f"bytes={pos}-")

    with urllib.request.build_opener().open(req, timeout=60) as r:
        resumed = pos and r.status == 206
        if not resumed:
            pos = 0
        total = int(r.headers.get("Content-Length") or 0) + pos
        read = pos
        if on_progress:
            on_progress(read, total)

        with open(part_path, "ab" if resumed else "wb") as f:
            while True:
                chunk = r.read(1048576)  # 1MB buffer
                if not chunk:
                    break
                f.write(chunk)
                read += len(chunk)
                if on_progress:
                    on_progress(read, total)

    part_path.replace(dest_path)
    return read


def get_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    parent = path.parent
    stem = path.stem
    suffix = path.suffix
    i = 2
    while True:
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1
