# Estado Atual da Sessão & Handoff

**Última Atualização:** 2026-10-31  
**Versão Atual:** `v0.3.0`  
**Branch Ativa:** `main`  
**Status dos Testes:** 32/32 suites passando (`unittest`)  
**Agente Responsável:** `global-master-agent` / `git-master-agent`

---

## 🎯 Entregas Concluídas na Versão v0.3.0

1. **💾 Save-Sync & Backup de Memory Cards:**
   - Módulo `src/rom_cli/core/savesync.py`.
   - Snapshot automático em `.zip` disparado ao fechar qualquer emulador.
   - Aba visual de "Saves & Backups" na GUI com histórico e botão "Restaurar Save".

2. **🇧🇷 Auto-Patcher de Traduções PT-BR:**
   - Módulo `src/rom_cli/core/patcher.py` (suporte a IPS e BPS em Python puro).
   - Botão "🔧 Traduzir" na lista da biblioteca e comando CLI `rom --patch`.

3. **🌐 Discord Rich Presence Nativo:**
   - Módulo `src/rom_cli/core/discord_rpc.py` via IPC Named Pipe nativo.
   - Atualização em tempo real de jogo, plataforma, poster e cronômetro.

4. **🔍 Auditor de BIOS de Emuladores:**
   - Módulo `src/rom_cli/core/bios_checker.py`.
   - Badges de integridade de BIOS na aba de Emuladores e comando CLI `rom --check-bios`.

5. **Testes & CI/CD:**
   - 32 testes unitários automatizados (100% passing).
   - Executável standalone `dist/ROM-Launcher.exe` recompilado.
