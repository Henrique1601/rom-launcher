"""Integração nativa com Discord Rich Presence via IPC Named Pipe (sem dependências externas).

Permite exibir no perfil do Discord qual jogo e plataforma o usuário está jogando,
com pôster, tempo de sessão decorrido e botões de compartilhamento.
"""

import json
import os
import struct
import sys
import threading
import time
import uuid
from typing import Optional, Dict, Any, Tuple

# Client ID padrão registrado para o ROM Launcher
DEFAULT_CLIENT_ID = "1203058863643795556"


class DiscordRPC:
    def __init__(self, client_id: str = DEFAULT_CLIENT_ID):
        self.client_id = client_id
        self._pipe = None
        self._connected = False
        self._start_time = None
        self._lock = threading.Lock()

    def _get_pipe_path(self) -> Optional[str]:
        """Localiza o endpoint do Discord IPC no sistema operacional."""
        if sys.platform == "win32":
            for i in range(10):
                path = f"\\\\.\\pipe\\discord-ipc-{i}"
                if os.path.exists(path):
                    return path
            return "\\\\.\\pipe\\discord-ipc-0"
        else:
            temp_dirs = [
                os.environ.get("XDG_RUNTIME_DIR", ""),
                os.environ.get("TMPDIR", ""),
                os.environ.get("TMP", ""),
                os.environ.get("TEMP", ""),
                "/tmp",
            ]
            for d in temp_dirs:
                if not d:
                    continue
                for i in range(10):
                    path = os.path.join(d, f"discord-ipc-{i}")
                    if os.path.exists(path):
                        return path
            return None

    def connect(self) -> bool:
        """Conecta-se ao pipe do Discord e envia o Handshake inicial."""
        with self._lock:
            if self._connected:
                return True

            path = self._get_pipe_path()
            if not path:
                return False

            try:
                if sys.platform == "win32":
                    # Abre o pipe nomeado no Windows
                    self._pipe = open(path, "w+b", buffering=0)
                else:
                    import socket
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.connect(path)
                    self._pipe = s

                # Envia Handshake Opcode 0
                handshake_payload = json.dumps({"v": 1, "client_id": self.client_id}).encode("utf-8")
                self._send(0, handshake_payload)

                # Lê resposta de confirmação
                op, resp = self._read()
                if op is not None:
                    self._connected = True
                    return True
            except Exception:
                self._pipe = None
                self._connected = False
                return False
            return False

    def _send(self, opcode: int, payload: bytes) -> None:
        """Envia um frame formatado (Opcode + Length + Payload)."""
        header = struct.pack("<II", opcode, len(payload))
        if sys.platform == "win32":
            self._pipe.write(header + payload)
            self._pipe.flush()
        else:
            self._pipe.sendall(header + payload)

    def _read(self) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """Lê um frame do pipe do Discord."""
        try:
            if sys.platform == "win32":
                header = self._pipe.read(8)
                if len(header) < 8:
                    return None, None
                opcode, length = struct.unpack("<II", header)
                data = self._pipe.read(length)
            else:
                header = self._pipe.recv(8)
                if len(header) < 8:
                    return None, None
                opcode, length = struct.unpack("<II", header)
                data = self._pipe.recv(length)
            return opcode, json.loads(data.decode("utf-8"))
        except Exception:
            return None, None

    def update_game_activity(self, game_title: str, platform_label: str, large_image_url: Optional[str] = None) -> bool:
        """Atualiza o status Rich Presence para o jogo atualmente em execução."""
        if not self._connected:
            if not self.connect():
                return False

        with self._lock:
            try:
                start_ts = int(time.time())
                activity = {
                    "details": game_title[:128],
                    "state": f"Plataforma: {platform_label}"[:128],
                    "timestamps": {
                        "start": start_ts
                    },
                    "assets": {
                        "large_image": large_image_url or "controller",
                        "large_text": game_title,
                        "small_image": "gamepad",
                        "small_text": f"Jogando no {platform_label}",
                    },
                    "buttons": [
                        {"label": "ROM Launcher", "url": "https://github.com/Henrique1601/rom-launcher"}
                    ]
                }

                payload = json.dumps({
                    "cmd": "SET_ACTIVITY",
                    "args": {
                        "pid": os.getpid(),
                        "activity": activity
                    },
                    "nonce": str(uuid.uuid4())
                }).encode("utf-8")

                self._send(1, payload)
                return True
            except Exception:
                self._connected = False
                return False

    def clear_activity(self) -> None:
        """Limpa a atividade e restaura o status neutro."""
        if not self._connected:
            return
        with self._lock:
            try:
                payload = json.dumps({
                    "cmd": "SET_ACTIVITY",
                    "args": {
                        "pid": os.getpid(),
                        "activity": None
                    },
                    "nonce": str(uuid.uuid4())
                }).encode("utf-8")
                self._send(1, payload)
            except Exception:
                pass

    def close(self) -> None:
        """Encerra a conexão com o Discord."""
        try:
            self.clear_activity()
            if self._pipe:
                self._pipe.close()
        except Exception:
            pass
        finally:
            self._pipe = None
            self._connected = False


# Instância global singleton para uso em todo o aplicativo
DISCORD = DiscordRPC()
