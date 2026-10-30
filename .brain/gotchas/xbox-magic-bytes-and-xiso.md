# Gotcha: Validação de Magic Bytes e Imagens de Xbox (OG e 360)

## Sintoma
Downloads de jogos de Xbox e Xbox 360 eram erroneamente marcados como arquivos inválidos ou não eram reconhecidos pelos emuladores (xemu e Xenia).

## Causa Raiz
1. Imagens Redump de Xbox Clássico utilizam partições de segurança que não são ISOs padrão de PC (requerem formato XISO).
2. Executáveis do Xbox utilizam assinaturas binárias específicas no header que não conferem com executáveis PE normais do Windows (`MZ`):
   - Xbox Clássico: `b"XBEH"` (Xbox Executable).
   - Xbox 360: `b"XEX2"` (Xbox 360 Executable).
   - Pacotes XBLA / DLCs: `b"LIVE"`, `b"CON "`, `b"PIRS"`.

## Solução Implementada
No módulo `src/rom_cli/core/validator.py`, adicionamos validação explícita para as extensões `.xbe`, `.xex`, `.god` e `.xiso`, checando os magic bytes corretos e bypassando verificações de ZIP padrão quando se trata de imagens de disco de grande porte.
