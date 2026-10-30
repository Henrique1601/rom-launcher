"""Utilitário de extração automática de arquivos (ZIP, 7z, RAR) pós-download."""

import os
import shutil
import zipfile
from pathlib import Path
from typing import Optional, Callable


def extract_archive(
    archive_path: Path,
    target_dir: Optional[Path] = None,
    remove_archive: bool = False,
    on_progress: Optional[Callable[[str], None]] = None
) -> Optional[Path]:
    """
    Extrai arquivos compactados suportados (.zip, .7z, .rar) para o diretório de destino.
    Retorna o caminho do diretório ou arquivo extraído principal.
    """
    archive_path = Path(archive_path)
    if not archive_path.exists():
        return None

    dest_dir = target_dir or archive_path.parent
    dest_dir.mkdir(parents=True, exist_ok=True)
    suffix = archive_path.suffix.lower()

    if suffix == ".zip":
        if on_progress:
            on_progress(f"Extraindo ZIP: {archive_path.name}...")
        try:
            with zipfile.ZipFile(archive_path, 'r') as z:
                z.extractall(dest_dir)
            if remove_archive:
                archive_path.unlink()
            return dest_dir
        except Exception as e:
            if on_progress:
                on_progress(f"Falha ao extrair ZIP ({e})")
            return None

    if suffix in (".7z", ".rar"):
        # Tenta utilizar py7zr se disponível, ou comando de sistema tar/7z
        if suffix == ".7z":
            try:
                import py7zr
                if on_progress:
                    on_progress(f"Extraindo 7z: {archive_path.name}...")
                with py7zr.SevenZipFile(archive_path, mode='r') as z:
                    z.extractall(path=dest_dir)
                if remove_archive:
                    archive_path.unlink()
                return dest_dir
            except ImportError:
                pass
            except Exception as e:
                if on_progress:
                    on_progress(f"Falha ao extrair 7z ({e})")
                return None

        # Fallback para utilitário de linha de comando se disponível (tar ou 7z)
        cmd_7z = shutil.which("7z") or shutil.which("7za")
        if cmd_7z:
            if on_progress:
                on_progress(f"Extraindo via 7z CLI: {archive_path.name}...")
            import subprocess
            res = subprocess.run([cmd_7z, "x", str(archive_path), f"-o{dest_dir}", "-y"], capture_output=True)
            if res.returncode == 0:
                if remove_archive:
                    archive_path.unlink()
                return dest_dir

        tar_cmd = shutil.which("tar")
        if tar_cmd and suffix == ".zip":
            import subprocess
            res = subprocess.run([tar_cmd, "-xf", str(archive_path), "-C", str(dest_dir)], capture_output=True)
            if res.returncode == 0:
                if remove_archive:
                    archive_path.unlink()
                return dest_dir

    return None
