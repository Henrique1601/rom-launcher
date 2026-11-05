"""Gerenciador e Instalador Automático de Emuladores Portáteis (Zero-Setup).

Permite baixar, extrair e registrar automaticamente versões portáteis oficiais
de emuladores diretamente do GitHub Releases e fontes recomendadas, sem necessidade
de configuração manual de executáveis.
"""

import io
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()
if sys.stdin is None:
    sys.stdin = io.StringIO()

from rom_cli.config import CACHE_DIR, UA
from rom_cli.core.extractor import extract_archive
from rom_cli.launcher.registry import EmulatorRegistry

EMULATORS_INSTALL_DIR = CACHE_DIR / "emulators"


@dataclass
class EmulatorCatalogEntry:
    id: str
    name: str
    platform_keys: List[str]
    binary_name: str
    github_repo: Optional[str]
    asset_pattern: str
    fallback_url: str
    expected_exe: str
    description: str


EMULATOR_CATALOG: Dict[str, EmulatorCatalogEntry] = {
    "duckstation": EmulatorCatalogEntry(
        id="duckstation",
        name="DuckStation",
        platform_keys=["ps1"],
        binary_name="duckstation",
        github_repo="stenzek/duckstation",
        asset_pattern=r"duckstation-windows-x64.*\.zip",
        fallback_url="https://github.com/stenzek/duckstation/releases/latest/download/duckstation-windows-x64-release.zip",
        expected_exe="duckstation-qt-x64-ReleaseLTCG.exe",
        description="Emulador de alta precisão e resolução para Sony PlayStation 1."
    ),
    "pcsx2": EmulatorCatalogEntry(
        id="pcsx2",
        name="PCSX2",
        platform_keys=["ps2"],
        binary_name="pcsx2",
        github_repo="PCSX2/pcsx2",
        asset_pattern=r"pcsx2-.*-windows-x64.*\.7z|pcsx2-.*-windows-x64.*\.zip",
        fallback_url="https://github.com/PCSX2/pcsx2/releases/latest/download/pcsx2-windows-x64-Qt.7z",
        expected_exe="pcsx2-qt.exe",
        description="Emulador oficial de PlayStation 2 com upscaling widescreen e suporte a texturas HD."
    ),
    "dolphin": EmulatorCatalogEntry(
        id="dolphin",
        name="Dolphin",
        platform_keys=["gc", "wii"],
        binary_name="dolphin",
        github_repo="dolphin-emu/dolphin",
        asset_pattern=r"dolphin-.*-x64\.7z|dolphin-.*-x64\.zip",
        fallback_url="https://dl.dolphin-emu.org/releases/2409/dolphin-2409-x64.7z",
        expected_exe="Dolphin.exe",
        description="Emulador com 4K/60FPS para Nintendo GameCube e Nintendo Wii."
    ),
    "mgba": EmulatorCatalogEntry(
        id="mgba",
        name="mGBA",
        platform_keys=["gba", "gb", "gbc"],
        binary_name="mgba",
        github_repo="mgba-emu/mgba",
        asset_pattern=r"mGBA-.*-win64\.7z|mGBA-.*-win64\.zip",
        fallback_url="https://github.com/mgba-emu/mgba/releases/download/0.10.3/mGBA-0.10.3-win64.7z",
        expected_exe="mGBA.exe",
        description="Emulador ultrarrápido e com cores precisas para Game Boy Advance, Color e Clássico."
    ),
    "snes9x": EmulatorCatalogEntry(
        id="snes9x",
        name="Snes9x",
        platform_keys=["snes"],
        binary_name="snes9x-x64",
        github_repo="snes9xgit/snes9x",
        asset_pattern=r"snes9x-.*-win32-x64\.zip",
        fallback_url="https://github.com/snes9xgit/snes9x/releases/download/1.62.3/snes9x-1.62.3-win32-x64.zip",
        expected_exe="snes9x-x64.exe",
        description="Emulador clássico consagrado de Super Nintendo com filtros CRT e suporte a shaders."
    ),
    "melonds": EmulatorCatalogEntry(
        id="melonds",
        name="melonDS",
        platform_keys=["nds"],
        binary_name="melonDS",
        github_repo="melonDS-emu/melonDS",
        asset_pattern=r"melonDS-.*-windows-x86_64\.zip",
        fallback_url="https://github.com/melonDS-emu/melonDS/releases/download/0.9.5/melonDS-0.9.5-windows-x86_64.zip",
        expected_exe="melonDS.exe",
        description="Emulador moderno de Nintendo DS com suporte a tela dividida, touch e multiplayer local."
    ),
    "ppsspp": EmulatorCatalogEntry(
        id="ppsspp",
        name="PPSSPP",
        platform_keys=["psp"],
        binary_name="PPSSPPWindows64",
        github_repo="hrydgard/ppsspp",
        asset_pattern=r"PPSSPPWindows64\.zip|ppsspp_win\.zip",
        fallback_url="https://www.ppsspp.org/files/1_17_1/ppsspp_win.zip",
        expected_exe="PPSSPPWindows64.exe",
        description="Emulador portátil de PlayStation Portable com suporte a 4K, 60fps e saves estendidos."
    ),
    "xemu": EmulatorCatalogEntry(
        id="xemu",
        name="xemu",
        platform_keys=["xbox"],
        binary_name="xemu",
        github_repo="xemu-project/xemu",
        asset_pattern=r"xemu-win-x86_64.*\.zip",
        fallback_url="https://github.com/xemu-project/xemu/releases/latest/download/xemu-win-x86_64-release.zip",
        expected_exe="xemu.exe",
        description="Emulador original do Xbox com suporte a Xbox Live Insignia e rendering em HD."
    ),
    "xenia": EmulatorCatalogEntry(
        id="xenia",
        name="Xenia",
        platform_keys=["xbox360"],
        binary_name="xenia",
        github_repo="xenia-project/release-builds",
        asset_pattern=r"xenia_master\.zip",
        fallback_url="https://github.com/xenia-project/release-builds/releases/latest/download/xenia_master.zip",
        expected_exe="xenia.exe",
        description="Emulador experimental de alta performance para Xbox 360 no Windows."
    ),
}

# Mapeamento rápido de platform_key para a entrada do catálogo
PLATFORM_TO_EMULATOR: Dict[str, str] = {
    "ps1": "duckstation",
    "ps2": "pcsx2",
    "gc": "dolphin",
    "wii": "dolphin",
    "gba": "mgba",
    "gb": "mgba",
    "gbc": "mgba",
    "snes": "snes9x",
    "nds": "melonds",
    "psp": "ppsspp",
    "xbox": "xemu",
    "xbox360": "xenia",
}


def get_emulator_info(identifier: str) -> Optional[EmulatorCatalogEntry]:
    """Retorna a configuração do emulador por id ou platform_key."""
    key = identifier.lower().strip()
    if key in EMULATOR_CATALOG:
        return EMULATOR_CATALOG[key]
    if key in PLATFORM_TO_EMULATOR:
        return EMULATOR_CATALOG[PLATFORM_TO_EMULATOR[key]]
    return None


def resolve_release_url(entry: EmulatorCatalogEntry) -> Tuple[str, str]:
    """Resolve a URL de download e o nome do arquivo, consultando a API do GitHub com fallback."""
    if entry.github_repo:
        api_url = f"https://api.github.com/repos/{entry.github_repo}/releases/latest"
        req = urllib.request.Request(api_url)
        req.add_header("User-Agent", UA)
        req.add_header("Accept", "application/vnd.github.v3+json")
        try:
            with urllib.request.build_opener().open(req, timeout=10) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    assets = data.get("assets", [])
                    regex = re.compile(entry.asset_pattern, re.IGNORECASE)
                    for asset in assets:
                        asset_name = asset.get("name", "")
                        if regex.search(asset_name):
                            download_url = asset.get("browser_download_url")
                            if download_url:
                                return download_url, asset_name
        except Exception:
            pass  # Fallback abaixo se atingir rate-limit ou timeout

    # Extrai o nome do arquivo a partir da URL de fallback
    parsed = urllib.parse.urlparse(entry.fallback_url)
    filename = Path(parsed.path).name or f"{entry.id}-portable.zip"
    return entry.fallback_url, filename


def download_file(
    url: str,
    dest_path: Path,
    on_progress: Optional[Callable[[int, int, str], None]] = None
) -> Path:
    """Faz o streaming do download de um arquivo com feedback de progresso."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)

    with urllib.request.build_opener().open(req, timeout=30) as response:
        total_size = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        chunk_size = 1024 * 64

        with open(dest_path, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if on_progress:
                    on_progress(downloaded, total_size, f"Baixando: {downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB")

    return dest_path


def find_executable(install_dir: Path, expected_name: str, binary_prefix: str) -> Optional[Path]:
    """Procura recursivamente pelo executável do emulador no diretório de instalação."""
    # 1. Checagem direta pelo nome exato esperado
    exact = install_dir / expected_name
    if exact.is_file():
        return exact

    # 2. Busca recursiva por executável com o mesmo nome
    matches = list(install_dir.rglob(expected_name))
    if matches and matches[0].is_file():
        return matches[0]

    # 3. Busca recursiva por qualquer .exe que contenha o prefixo do binário
    prefix_clean = binary_prefix.lower()
    for exe in install_dir.rglob("*.exe"):
        if prefix_clean in exe.stem.lower():
            return exe

    # 4. Fallback: o primeiro executável encontrado que não seja unins/updater
    candidates = [
        p for p in install_dir.rglob("*.exe")
        if not any(skip in p.name.lower() for skip in ("unins", "setup", "update", "crash"))
    ]
    if candidates:
        return candidates[0]

    return None


def install_emulator(
    identifier: str,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
    registry: Optional[EmulatorRegistry] = None
) -> Tuple[bool, str, Optional[str]]:
    """Baixa, extrai e registra o emulador correspondente ao identificador (ex: 'ps1', 'duckstation').

    Retorna: (sucesso: bool, mensagem: str, caminho_exe: Optional[str])
    """
    entry = get_emulator_info(identifier)
    if not entry:
        return False, f"Emulador '{identifier}' não encontrado no catálogo oficial.", None

    target_dir = EMULATORS_INSTALL_DIR / entry.id
    target_dir.mkdir(parents=True, exist_ok=True)

    if on_progress:
        on_progress(0, 100, f"Consultando última release de {entry.name}...")

    try:
        download_url, filename = resolve_release_url(entry)
    except Exception as e:
        return False, f"Falha ao obter URL de download para {entry.name}: {e}", None

    archive_path = target_dir / filename

    try:
        if on_progress:
            on_progress(10, 100, f"Baixando pacote portátil ({filename})...")
        download_file(download_url, archive_path, on_progress)
    except Exception as e:
        return False, f"Erro ao baixar {entry.name}: {e}", None

    if on_progress:
        on_progress(80, 100, f"Extraindo arquivos de {entry.name}...")

    # Extrai arquivo
    extracted_ok = False
    if archive_path.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(archive_path, "r") as z:
                z.extractall(target_dir)
            extracted_ok = True
        except Exception:
            extracted_ok = False

    if not extracted_ok:
        res = extract_archive(archive_path, target_dir=target_dir)
        extracted_ok = res is not None

    # Remove o arquivo compactado após a extração para poupar espaço em disco
    try:
        if archive_path.exists():
            archive_path.unlink()
    except Exception:
        pass

    if not extracted_ok:
        return False, f"Falha ao descompactar {filename}. Formato não suportado ou corrompido.", None

    if on_progress:
        on_progress(95, 100, "Localizando executável e configurando atalhos...")

    exe_path = find_executable(target_dir, entry.expected_exe, entry.binary_name)
    if not exe_path or not exe_path.is_file():
        return False, f"Instalado em {target_dir}, mas o executável '{entry.expected_exe}' não foi localizado.", None

    # Registra no EmulatorRegistry
    reg = registry or EmulatorRegistry()
    for pk in entry.platform_keys:
        reg.set_emulator_path(pk, str(exe_path))

    if on_progress:
        on_progress(100, 100, f"✔ {entry.name} configurado com sucesso!")

    return True, f"✔ {entry.name} instalado e configurado em {exe_path}", str(exe_path)
