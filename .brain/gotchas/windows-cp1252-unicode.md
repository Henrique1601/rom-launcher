# Gotcha: Falhas de UnicodeEncodeError no Terminal Windows (CP1252)

## Sintoma
Ao executar comandos de terminal como `rom --installed`, o Python crashava com:
`UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f3ae' in position 4: character maps to <undefined>`.

## Causa Raiz
No Windows em português (Brasil), o console padrão (PowerShell ou CMD) frequentemente opera na tabela de códigos ANSI de página `cp1252` em vez de UTF-8. Caracteres Unicode fora do conjunto ANSI (como emojis de gamepad 🎮 e estrelas ★) não conseguem ser serializados pelo stream padrão `sys.stdout`.

## Solução Implementada
No módulo `src/rom_cli/core/utils.py`, a função `write()` foi encapsulada com bloco `try/except UnicodeEncodeError`. Caso ocorra o erro de codificação, o texto é automaticamente sanitizado através de:
```python
safe_text = text.encode(sys.stdout.encoding or "ascii", errors="replace").decode(sys.stdout.encoding or "ascii")
```
Isso garante que o programa continue executando normalmente em qualquer terminal Windows, substituindo o glifo não suportado por um caractere seguro sem quebrar o fluxo.
