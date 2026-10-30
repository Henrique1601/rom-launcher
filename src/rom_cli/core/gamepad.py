"""Suporte nativo a controles (Gamepad / XInput) no Windows sem dependências externas."""

import ctypes
import os
import sys
import threading
import time
from typing import Callable, Optional

# Botões do XInput
DPAD_UP = 0x0001
DPAD_DOWN = 0x0002
DPAD_LEFT = 0x0004
DPAD_RIGHT = 0x0008
START = 0x0010
BACK = 0x0020
LEFT_SHOULDER = 0x0100
RIGHT_SHOULDER = 0x0200
BUTTON_A = 0x1000
BUTTON_B = 0x2000
BUTTON_X = 0x4000
BUTTON_Y = 0x8000


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


class GamepadController:
    """Monitor de controle Xbox/XInput em segundo plano para modo sofá."""

    def __init__(self):
        self.xinput = self._load_xinput()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_buttons = 0
        self._last_trigger_time = 0.0

        # Callbacks de navegação
        self.on_up: Optional[Callable[[], None]] = None
        self.on_down: Optional[Callable[[], None]] = None
        self.on_left: Optional[Callable[[], None]] = None
        self.on_right: Optional[Callable[[], None]] = None
        self.on_a: Optional[Callable[[], None]] = None
        self.on_b: Optional[Callable[[], None]] = None
        self.on_x: Optional[Callable[[], None]] = None
        self.on_y: Optional[Callable[[], None]] = None
        self.on_lb: Optional[Callable[[], None]] = None
        self.on_rb: Optional[Callable[[], None]] = None

    def _load_xinput(self):
        if sys.platform != "win32":
            return None
        for dll_name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
            try:
                return ctypes.windll.LoadLibrary(dll_name)
            except Exception:
                continue
        return None

    def is_available(self) -> bool:
        return self.xinput is not None

    def is_connected(self, user_index: int = 0) -> bool:
        if not self.xinput:
            return False
        state = XINPUT_STATE()
        res = self.xinput.XInputGetState(user_index, ctypes.byref(state))
        return res == 0

    def start(self):
        if not self.xinput or self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _poll_loop(self):
        state = XINPUT_STATE()
        deadzone = 12000

        while self._running:
            try:
                res = self.xinput.XInputGetState(0, ctypes.byref(state))
                if res == 0:
                    buttons = state.Gamepad.wButtons
                    now = time.time()
                    newly_pressed = buttons & ~self._last_buttons

                    # Analógico esquerdo como direcional
                    lx = state.Gamepad.sThumbLX
                    ly = state.Gamepad.sThumbLY

                    # Cooldown de 150ms para evitar disparos repetidos ultra rápidos
                    can_trigger = (now - self._last_trigger_time) > 0.16

                    if can_trigger:
                        if (newly_pressed & DPAD_UP) or (ly > deadzone and abs(lx) < ly):
                            if self.on_up:
                                self.on_up()
                            self._last_trigger_time = now
                        elif (newly_pressed & DPAD_DOWN) or (ly < -deadzone and abs(lx) < abs(ly)):
                            if self.on_down:
                                self.on_down()
                            self._last_trigger_time = now
                        elif (newly_pressed & DPAD_LEFT) or (lx < -deadzone and abs(ly) < abs(lx)):
                            if self.on_left:
                                self.on_left()
                            self._last_trigger_time = now
                        elif (newly_pressed & DPAD_RIGHT) or (lx > deadzone and abs(ly) < lx):
                            if self.on_right:
                                self.on_right()
                            self._last_trigger_time = now

                    if newly_pressed & BUTTON_A:
                        if self.on_a:
                            self.on_a()
                    elif newly_pressed & BUTTON_B:
                        if self.on_b:
                            self.on_b()
                    elif newly_pressed & BUTTON_X:
                        if self.on_x:
                            self.on_x()
                    elif newly_pressed & BUTTON_Y:
                        if self.on_y:
                            self.on_y()
                    elif newly_pressed & LEFT_SHOULDER:
                        if self.on_lb:
                            self.on_lb()
                    elif newly_pressed & RIGHT_SHOULDER:
                        if self.on_rb:
                            self.on_rb()

                    self._last_buttons = buttons
                else:
                    self._last_buttons = 0
            except Exception:
                pass
            time.sleep(0.04)  # ~25 polling ticks por segundo


GAMEPAD = GamepadController()
