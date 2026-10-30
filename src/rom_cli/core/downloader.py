"""Motor de download com suporte a HTTP Range (retomada), chunks paralelos e barra de progresso."""

import os
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Optional, Tuple, Union

from rom_cli.config import UA
from rom_cli.core.utils import human_size, safe_name
from rom_cli.core.validator import validate_file, fix_magic_extension
from rom_cli.models import RomItem


def get_remote_file_info(url: str, referer: Optional[str] = None) -> Tuple[int, bool]:
    """Obtém o tamanho do arquivo remoto e se o servidor aceita Range requests (HTTP 206)."""
    req = urllib.request.Request(url, method="HEAD")
    req.add_header("User-Agent", UA)
    if referer:
        req.add_header("Referer", referer)

    try:
        with urllib.request.build_opener().open(req, timeout=15) as r:
            length = int(r.headers.get("Content-Length") or 0)
            accept_ranges = "bytes" in r.headers.get("Accept-Ranges", "").lower()
            return length, accept_ranges
    except Exception:
        pass

    # Fallback caso HEAD seja bloqueado: tenta um GET de 1 byte
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    req.add_header("Range", "bytes=0-0")
    if referer:
        req.add_header("Referer", referer)

    try:
        with urllib.request.build_opener().open(req, timeout=15) as r:
            cr = r.headers.get("Content-Range", "")
            if "/" in cr:
                length = int(cr.split("/")[-1])
                return length, (r.status == 206)
            return int(r.headers.get("Content-Length") or 0), False
    except Exception:
        return 0, False


def stream_download_parallel(
    url: str,
    dest_path: Path,
    referer: Optional[str] = None,
    threads: int = 4,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> int:
    """Download acelerado em múltiplos threads para servidores que suportam HTTP Range."""
    total_size, supports_range = get_remote_file_info(url, referer)

    # Se não suporta range ou é menor que 5MB, usa o download de conexão única
    if not supports_range or total_size < 5 * 1024 * 1024:
        return stream_download_single(url, dest_path, referer, on_progress)

    part_path = dest_path.with_suffix(dest_path.suffix + ".part")
    # Aloca espaço inicial se possível
    with open(part_path, "wb") as f:
        f.seek(total_size - 1)
        f.write(b"\0")

    chunk_size = total_size // threads
    ranges = []
    for i in range(threads):
        start = i * chunk_size
        end = total_size - 1 if i == threads - 1 else (i + 1) * chunk_size - 1
        ranges.append((start, end))

    lock = threading.Lock()
    bytes_downloaded = [0]

    def download_chunk(range_bounds):
        start_byte, end_byte = range_bounds
        req = urllib.request.Request(url)
        req.add_header("User-Agent", UA)
        if referer:
            req.add_header("Referer", referer)
        req.add_header("Range", f"bytes={start_byte}-{end_byte}")

        with urllib.request.build_opener().open(req, timeout=60) as r:
            cur_pos = start_byte
            while True:
                data = r.read(262144)  # 256KB
                if not data:
                    break
                with lock:
                    with open(part_path, "r+b") as f:
                        f.seek(cur_pos)
                        f.write(data)
                    bytes_downloaded[0] += len(data)
                    if on_progress:
                        on_progress(bytes_downloaded[0], total_size)
                cur_pos += len(data)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        list(executor.map(download_chunk, ranges))

    part_path.replace(dest_path)
    return total_size


def stream_download_single(
    url: str,
    dest_path: Path,
    referer: Optional[str] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> int:
    """Download sequencial com retomada (Range: bytes=pos-)."""
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


# Aliases padrão
stream_download = stream_download_parallel


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
