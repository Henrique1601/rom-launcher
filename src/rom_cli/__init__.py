"""EmuCraft - Central e Launcher de Emulação, Preservação e Download de ROMs."""

import io
import sys

# Protege ambientes GUI do Windows (--noconsole / pythonw) onde stdio pode ser None
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()
if sys.stdin is None:
    sys.stdin = io.StringIO()

__version__ = "1.1.0"
