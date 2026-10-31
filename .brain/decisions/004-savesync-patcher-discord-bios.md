# ADR-004: Save-Sync, Auto-Patcher PT-BR, Discord RPC e Auditor de BIOS

## Status
Aceito (v0.3.0)

## Contexto
O ecossistema inicial provia download, catalogação, verificação de integridade e lançamento de jogos. Para atingir paridade com suítes de emulação premium (como EmuDeck e Playnite), quatro funcionalidades críticas eram necessárias:
1. Prevenção de perda de progresso (saves e memory cards espalhados em pastas ocultas de emuladores).
2. Acessibilidade de ROM hacks e traduções de fãs brasileiras sem exigir executáveis legados de 32 bits (Lunar IPS).
3. Engajamento social e presença online (Discord Rich Presence).
4. Redução de atrito com usuários novatos devido à ausência de BIOS e chaves nos emuladores.

## Decisões
1. **Save-Sync Automático (`core/savesync.py`):**
   - Mapeamento dinâmico de diretórios de saves para 10+ emuladores.
   - Criação de snapshots ZIP rotacionados (máximo de 5 cópias) disparados automaticamente ao encerrar qualquer sessão de jogo (`launcher.py`).
   - Interface visual para restaurar snapshots corrompidos com 1 clique.

2. **Auto-Patcher em Python Puro (`core/patcher.py`):**
   - Implementação nativa dos algoritmos IPS (registros padrão e RLE) e BPS (Beat Patch System com VLQ).
   - Elimina dependências externas como Lunar IPS ou Flips, operando tanto via GUI quanto CLI (`rom --patch <rom> <patch>`).

3. **Discord Rich Presence Nativo (`core/discord_rpc.py`):**
   - Implementação de cliente IPC sobre Windows Named Pipe (`\\.\pipe\discord-ipc-0`) e Unix domain sockets com zero dependências externas.
   - Ativação assíncrona com fallback silencioso quando o Discord não estiver em execução.

4. **Auditor de BIOS (`core/bios_checker.py`):**
   - Verificação heurística e de nomes recomendados para PS1, PS2, PS3, Switch, Xbox e RetroArch.
   - Exibição visual com badges de status (🟢 BIOS OK / 🔴 BIOS Ausente) na aba de Emuladores da GUI e CLI (`rom --check-bios`).

## Consequências
- Aumento de 21 para 32 testes unitários automatizados cobrindo 100% dos novos módulos.
- Zero dependências de pacotes de terceiros adicionadas (tudo implementado na biblioteca padrão do Python).
