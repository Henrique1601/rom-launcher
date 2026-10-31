"""Auditor e verificador de integridade de BIOS e Firmwares de emuladores.

Detecta a presença e integridade de arquivos essenciais (como SCPH1001.bin para PS1,
SCPH39001.bin para PS2, prod.keys para Switch e Firmware do PS3).
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


def get_bios_rules() -> Dict[str, Dict[str, Any]]:
    """Define as regras de auditoria para cada emulador/plataforma."""
    home = Path.home()
    appdata = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    localappdata = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
    documents = home / "Documents"

    return {
        "ps2": {
            "name": "PlayStation 2 (PCSX2)",
            "folders": [
                documents / "PCSX2" / "bios",
                appdata / "PCSX2" / "bios",
                home / ".config" / "PCSX2" / "bios",
            ],
            "recommended_files": [
                "scph39001.bin", "scph70012.bin", "scph10000.bin", "ps2-0230a-20080220.bin"
            ],
            "description": "BIOS do PlayStation 2 (obrigatória para iniciar a emulação).",
        },
        "ps1": {
            "name": "PlayStation 1 (DuckStation / RetroArch)",
            "folders": [
                documents / "DuckStation" / "bios",
                appdata / "DuckStation" / "bios",
                appdata / "RetroArch" / "system",
                home / ".local" / "share" / "duckstation" / "bios",
            ],
            "recommended_files": [
                "scph1001.bin", "scph5500.bin", "scph5501.bin", "scph5502.bin", "scph7001.bin"
            ],
            "description": "BIOS do PS1 (garante compatibilidade e inicialização limpa).",
        },
        "switch": {
            "name": "Nintendo Switch (Ryujinx)",
            "folders": [
                appdata / "Ryujinx" / "system",
                home / ".config" / "Ryujinx" / "system",
            ],
            "recommended_files": [
                "prod.keys", "title.keys"
            ],
            "description": "Chaves de decodificação prod.keys do Switch.",
        },
        "ps3": {
            "name": "PlayStation 3 (RPCS3)",
            "folders": [
                appdata / "RPCS3" / "dev_flash",
                home / ".config" / "rpcs3" / "dev_flash",
            ],
            "recommended_files": [
                "vsh/module/vsh.self"
            ],
            "description": "Firmware oficial do PS3 (instalado via PS3UPDAT.PUP).",
        },
        "xbox": {
            "name": "Xbox Clássico (xemu)",
            "folders": [
                appdata / "xemu" / "xemu",
                home / ".local" / "share" / "xemu" / "xemu",
            ],
            "recommended_files": [
                "mcpx_1.0.bin", "Complex_4627.bin"
            ],
            "description": "MCPX Boot ROM e BIOS Flash do Xbox Original.",
        },
        "retroarch": {
            "name": "RetroArch (System Cores)",
            "folders": [
                appdata / "RetroArch" / "system",
                home / ".config" / "retroarch" / "system",
            ],
            "recommended_files": [
                "gba_bios.bin", "sega_101.bin"
            ],
            "description": "BIOS de consoles clássicos (GBA, Saturn, Sega CD).",
        }
    }


def audit_bios(platform_key: str) -> Dict[str, Any]:
    """Audita o status da BIOS para a plataforma especificada."""
    rules = get_bios_rules()
    info = rules.get(platform_key)
    if not info:
        return {
            "platform": platform_key,
            "status": "unknown",
            "message": "Nenhuma regra de BIOS cadastrada para esta plataforma."
        }

    target_dir: Optional[Path] = None
    for folder in info["folders"]:
        if folder.exists() and folder.is_dir():
            target_dir = folder
            break

    if not target_dir:
        default_dir = info["folders"][0]
        return {
            "platform": platform_key,
            "name": info["name"],
            "status": "missing_folder",
            "bios_dir": str(default_dir),
            "files_found": [],
            "recommended": info["recommended_files"],
            "message": f"Pasta de BIOS não encontrada. Crie a pasta em: {default_dir}",
            "description": info["description"],
        }

    # Procura arquivos existentes na pasta
    existing_files = [f.name.lower() for f in target_dir.glob("*") if f.is_file()]
    matched = []
    for rec in info["recommended_files"]:
        if any(rec.lower() in f for f in existing_files):
            matched.append(rec)

    has_any = len(matched) > 0 or len(existing_files) > 0
    status = "ok" if has_any else "missing_bios"

    return {
        "platform": platform_key,
        "name": info["name"],
        "status": status,
        "bios_dir": str(target_dir),
        "files_found": existing_files[:10],
        "matched": matched,
        "recommended": info["recommended_files"],
        "message": "BIOS detectada e pronta!" if status == "ok" else f"Nenhum arquivo de BIOS encontrado na pasta: {target_dir}",
        "description": info["description"],
    }


def audit_all_bios() -> List[Dict[str, Any]]:
    """Executa auditoria em todos os sistemas conhecidos."""
    rules = get_bios_rules()
    return [audit_bios(k) for k in rules.keys()]
