"""Motor de aplicação de patches de tradução e ROM hacks (formatos IPS e BPS).

Permite aplicar traduções de fãs brasileiras (PT-BR) e correções diretamente
nas ROMs sem precisar de utilitários externos (como Lunar IPS ou Flips).
"""

import struct
import zlib
from pathlib import Path
from typing import Optional, Tuple, Union


class PatchError(Exception):
    """Exceção levantada quando um patch é inválido ou incompatível."""
    pass


def apply_ips_patch(rom_bytes: bytes, patch_bytes: bytes) -> bytes:
    """Aplica um patch IPS padrão em uma ROM e retorna os novos bytes."""
    if not patch_bytes.startswith(b"PATCH"):
        raise PatchError("Arquivo IPS inválido: cabeçalho 'PATCH' ausente.")

    target = bytearray(rom_bytes)
    offset = 5
    patch_len = len(patch_bytes)

    while offset < patch_len:
        if offset + 3 > patch_len:
            break

        # Verifica marcador de fim EOF
        if patch_bytes[offset:offset + 3] == b"EOF":
            offset += 3
            # Truncamento opcional de 3 bytes após EOF
            if offset + 3 <= patch_len:
                truncate_len = int.from_bytes(patch_bytes[offset:offset + 3], "big")
                if len(target) > truncate_len:
                    target = target[:truncate_len]
            break

        dest_offset = int.from_bytes(patch_bytes[offset:offset + 3], "big")
        offset += 3

        if offset + 2 > patch_len:
            raise PatchError("Patch IPS corrompido: tamanho de registro incompleto.")

        size = int.from_bytes(patch_bytes[offset:offset + 2], "big")
        offset += 2

        if size == 0:
            # Modo RLE (Run-Length Encoded)
            if offset + 3 > patch_len:
                raise PatchError("Patch IPS corrompido no bloco RLE.")
            rle_count = int.from_bytes(patch_bytes[offset:offset + 2], "big")
            rle_val = patch_bytes[offset + 2]
            offset += 3

            # Expande a ROM se necessário
            if dest_offset + rle_count > len(target):
                target.extend(b"\x00" * (dest_offset + rle_count - len(target)))
            target[dest_offset:dest_offset + rle_count] = bytes([rle_val]) * rle_count
        else:
            # Modo Padrão
            if offset + size > patch_len:
                raise PatchError("Patch IPS corrompido: dados de registro menores que o tamanho esperado.")
            data = patch_bytes[offset:offset + size]
            offset += size

            # Expande a ROM se necessário
            if dest_offset + size > len(target):
                target.extend(b"\x00" * (dest_offset + size - len(target)))
            target[dest_offset:dest_offset + size] = data

    return bytes(target)


def _read_bps_varint(data: bytes, offset: int) -> Tuple[int, int]:
    """Lê um inteiro de tamanho variável (VLQ) de um patch BPS."""
    result = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise PatchError("Patch BPS corrompido ao ler número variável.")
        b = data[offset]
        offset += 1
        result += (b & 0x7F) << shift
        if b & 0x80:
            break
        shift += 7
        result += 1 << shift
    return result, offset


def apply_bps_patch(rom_bytes: bytes, patch_bytes: bytes, verify_crc: bool = True) -> bytes:
    """Aplica um patch BPS (Beat Patch System) moderno em uma ROM."""
    if not patch_bytes.startswith(b"BPS1"):
        raise PatchError("Arquivo BPS inválido: cabeçalho 'BPS1' ausente.")

    if len(patch_bytes) < 16:
        raise PatchError("Patch BPS muito curto ou corrompido.")

    offset = 4
    source_len, offset = _read_bps_varint(patch_bytes, offset)
    target_len, offset = _read_bps_varint(patch_bytes, offset)
    metadata_len, offset = _read_bps_varint(patch_bytes, offset)

    # Pula os metadados XML/JSON opcionais
    offset += metadata_len

    source = bytearray(rom_bytes)
    target = bytearray(target_len)

    out_offset = 0
    source_rel = 0
    target_rel = 0
    patch_data_end = len(patch_bytes) - 12  # Últimos 12 bytes são CRCs

    while offset < patch_data_end:
        cmd, offset = _read_bps_varint(patch_bytes, offset)
        action = cmd & 3
        length = (cmd >> 2) + 1

        if action == 0:
            # SourceRead
            target[out_offset:out_offset + length] = source[out_offset:out_offset + length]
            out_offset += length
        elif action == 1:
            # TargetRead
            target[out_offset:out_offset + length] = patch_bytes[offset:offset + length]
            offset += length
            out_offset += length
        elif action == 2:
            # SourceCopy
            offset_shift, offset = _read_bps_varint(patch_bytes, offset)
            if offset_shift & 1:
                source_rel -= (offset_shift >> 1) + 1
            else:
                source_rel += offset_shift >> 1
            target[out_offset:out_offset + length] = source[source_rel:source_rel + length]
            out_offset += length
            source_rel += length
        elif action == 3:
            # TargetCopy
            offset_shift, offset = _read_bps_varint(patch_bytes, offset)
            if offset_shift & 1:
                target_rel -= (offset_shift >> 1) + 1
            else:
                target_rel += offset_shift >> 1
            while length > 0:
                chunk = min(length, out_offset - target_rel)
                if chunk <= 0:
                    chunk = 1
                target[out_offset:out_offset + chunk] = target[target_rel:target_rel + chunk]
                out_offset += chunk
                target_rel += chunk
                length -= chunk

    return bytes(target)


def apply_patch(rom_path: Union[str, Path], patch_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path:
    """Detecta automaticamente o formato do patch (IPS ou BPS) e gera a ROM traduzida."""
    rom_p = Path(rom_path)
    patch_p = Path(patch_path)

    if not rom_p.exists():
        raise FileNotFoundError(f"Arquivo de ROM não encontrado: {rom_p}")
    if not patch_p.exists():
        raise FileNotFoundError(f"Arquivo de patch não encontrado: {patch_p}")

    rom_data = rom_p.read_bytes()
    patch_data = patch_p.read_bytes()

    if patch_data.startswith(b"PATCH") or patch_p.suffix.lower() == ".ips":
        patched_data = apply_ips_patch(rom_data, patch_data)
    elif patch_data.startswith(b"BPS1") or patch_p.suffix.lower() == ".bps":
        patched_data = apply_bps_patch(rom_data, patch_data)
    else:
        raise PatchError(f"Formato de patch não suportado para {patch_p.name}. Use .ips ou .bps.")

    if not output_path:
        # Gera nome com [PT-BR] por padrão
        stem = rom_p.stem
        output_path = rom_p.parent / f"{stem} [PT-BR]{rom_p.suffix}"

    out_p = Path(output_path)
    out_p.write_bytes(patched_data)
    return out_p
