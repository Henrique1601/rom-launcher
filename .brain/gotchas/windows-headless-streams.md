# Gotcha: `sys.stdout` e `sys.stderr` são `None` em Apps GUI Windows

## Contexto
Ao rodar Python no Windows sem console (seja através de `pythonw.exe`, VBScript `wscript.exe`, ou empacotado via PyInstaller `--noconsole` / `--windowed`), o Windows não anexa manipuladores de console padrão (`CONOUT$`, `CONIN$`).

Nessas condições, o interpretador Python inicializa:
- `sys.stdout = None`
- `sys.stderr = None`
- `sys.stdin = None`

## O Erro
Qualquer chamada a `sys.stdout.isatty()`, `sys.stdout.write(...)` ou `print(...)` dispara:
```text
AttributeError: 'NoneType' object has no attribute 'isatty'
```
ou
```text
AttributeError: 'NoneType' object has no attribute 'write'
```

## Solução Arquitetural Aplicada
1. **Fallback Global para Streams em Memória:**
   No topo do módulo de entrada (`main_window.py`), no `__init__.py` e em `core/utils.py`:
   ```python
   import io
   import sys

   if sys.stdout is None:
       sys.stdout = io.StringIO()
   if sys.stderr is None:
       sys.stderr = io.StringIO()
   if sys.stdin is None:
       sys.stdin = io.StringIO()
   ```

2. **Checagem Segura de TTY:**
   ```python
   TTY = bool(sys.stdout and hasattr(sys.stdout, "isatty") and sys.stdout.isatty())
   ```

3. **Escrita Resiliente em `utils.write()`:**
   Verifica se `sys.stdout is None` antes de tentar escrever e captura qualquer falha silenciosamente.
