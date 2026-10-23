"""Validação de integridade e magic bytes de arquivos de ROM."""

import os
from pathlib import Path
from typing import Union
import zipfile


def validate_file(path: Union[str, Path]) -> bool:
    """Valida se o arquivo baixado é íntegro e não está corrompido/vazio."""
    path = Path(path)
    if not path.exists():
        return False

    size = path.stat().st_size
    if size < 1024:
        # Arquivo menor que 1KB geralmente é página de erro HTML ou resposta de link expirado
        return False

    # Acima de 50MB, validação leve por magic byte ou aceitação rápida
    if size > 50 * 1024 * 1024:
        return True

    name = path.name.lower()
    try:
        if name.endswith(".zip"):
            with open(path, "rb") as f:
                head = f.read(4)
            return head.startswith(b"PK") or zipfile.is_zipfile(path)

        if name.endswith(".7z"):
            with open(path, "rb") as f:
                return f.read(3) == b"7z\xbc"

        if name.endswith(".nsp"):
            with open(path, "rb") as f:
                return f.read(4) == b"PFS0"

        if name.endswith(".pkg"):
            with open(path, "rb") as f:
                return f.read(4) in (b"\x7fPKG", b"\x7fCNT")
    except (OSError, Exception):
        return False

    return True


def fix_magic_extension(path: Union[str, Path]) -> Path:
    """Corrige a extensão do arquivo caso o cabeçalho real divirja do nome."""
    path = Path(path)
    try:
        with open(path, "rb") as f:
            head = f.read(8)
    except OSError:
        return path

    magic_map = (
        (b"PK\x03\x04", ".zip"),
        (b"Rar!", ".rar"),
        (b"7z\xbc", ".7z"),
        (b"PFS0", ".nsp"),
        (b"HEAD", ".xci"),
        (b"\x7fPKG", ".pkg"),
        (b"\x7fCNT", ".pkg"),
    )

    for magic, ext in magic_map:
        if head.startswith(magic):
            if path.suffix.lower() != ext:
                new_path = path.with_suffix(ext)
                # Garante caminho único
                i = 2
                while new_path.exists():
                    new_path = path.parent / f"{path.stem} ({i}){ext}"
                    i += 1
                path.rename(new_path)
                return new_path
            return path

    return path
