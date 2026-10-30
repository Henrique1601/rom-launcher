# 📐 Regras de Engenharia & Padrões de Código

> **Status:** Ativo  
> **Escopo:** Todo o repositório

---

## 1. Tratamento Cross-Platform & Windows
1. **Paths com `pathlib.Path`:** Nunca concatenar caminhos com barras manuais (`/` ou `\`). Sempre use `Path` ou `Join-Path`.
2. **Resolução de Diretórios do Usuário:**
   - Pasta de ROMs padrão: `Path.home() / "Downloads" / "roms"`.
   - Pasta de Cache: Usar `%LOCALAPPDATA%\rom-cli` no Windows e `~/.cache/rom-cli` em Unix.
3. **Encoding Seguro no Terminal (Anti-Crash `cp1252`):**
   - O terminal padrão do Windows frequentemente usa codificação `cp1252` em vez de `utf-8`.
   - Qualquer saída com emojis deve passar por `utils.write()` com fallback de substituição (`errors="replace"`), evitando `UnicodeEncodeError`.

---

## 2. Interface Gráfica (CustomTkinter) & Concorrência
1. **Nunca Travar a UI (Thread-Safe):**
   - Requisições HTTP, downloads, descompactação e busca de capas **devem** ser executados em background threads (`threading.Thread(..., daemon=True)`).
   - Atualizações em elementos do CustomTkinter vindas de threads secundárias **devem** ser agendadas na main thread via `widget.after(0, callback)`.
2. **Cache Agressivo de Imagens:**
   - Capas redimensionadas devem ser cacheadas em memória (`cover_cache`) com instâncias reutilizadas de `CTkImage` para evitar garbage collection constante e engasgos de rolagem.

---

## 3. Provedores de ROMs & Downloads
1. **Suporte Obrigatório a Retomada (`HTTP Range`):**
   - Todo download grava primeiro em arquivo temporário com sufixo `.part`.
   - Se interrompido, deve tentar retomar enviando o header `Range: bytes={pos}-`.
2. **Validação de Integridade (Magic Bytes):**
   - Arquivos menores que 1024 bytes após o download devem ser rejeitados (geralmente são páginas HTML de erro ou links expirados).
   - Verificar cabeçalhos de arquivo reais (`PFS0` para Switch, `PKG` para Sony, `XBEH`/`XEX2` para Xbox).
