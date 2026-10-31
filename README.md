# 🎮 EmuCraft (rom-cli)

[![CI](https://github.com/Henrique1601/emucraft/actions/workflows/ci.yml/badge.svg)](https://github.com/Henrique1601/emucraft/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

> **EmuCraft — Plataforma gamer completa de preservação, download e inicialização de jogos clássicos e modernos.**  
> Equipada com interface gráfica moderna no estilo **Liquid Glass & Motion** (**CustomTkinter**), interface de terminal interativa (**Textual TUI**) e CLI ultrarrápida com motor paralelo multi-chunk.

---

## ✨ Principais Funcionalidades

- 🎮 **Suporte Completo a 28+ Plataformas:** Nintendo (Switch a NES), PlayStation (PS1 a PS5, PSP, Vita), Família Xbox (Xbox Original, Xbox 360, XBLA), Sega, Arcade e PC.
- 💎 **Interface Gamer Liquid Glass & Motion:** Hero Banner dinâmico com arte panorâmica, barra de filtros rápidos (Pills), hover glow neon e feedback sonoro de micro-interações.
- 💾 **Save-Sync & Backup de Memory Cards:** Snapshots automáticos de saves ao encerrar sessões (PCSX2, Dolphin, DuckStation, RPCS3, Ryujinx, RetroArch).
- 🇧🇷 **Auto-Patcher de Traduções PT-BR:** Aplica patches `.ips` e `.bps` de fãs brasileiros diretamente na ROM com 1 clique (na GUI ou CLI).
- 🌐 **Discord Rich Presence Nativo:** Mostra em tempo real no seu perfil do Discord qual jogo e console você está jogando, com poster oficial e tempo de sessão.
- 🔍 **Auditor de BIOS de Emuladores:** Diagnostica a integridade e presença de BIOS/Firmwares (PS1, PS2, PS3, Switch, Xbox).
- 🖼️ **Box Art Auto-Scraper:** Download automático de capas oficiais (2D/3D) via *Libretro Thumbnails* com cache local.
- 🏆 **RetroAchievements Integrado:** Consulta de conquistas, badges, pontuação e progresso via API pública oficial do RetroAchievements.
- 🕹️ **Couch / Gamepad Mode:** Navegação nativa por controle (Xbox/XInput via `ctypes`) para jogar direto do sofá com D-pad, botões A/B/X/Y e gatilhos.
- 🎲 **Roleta Gamer (Gamer Roulette):** Sorteio inteligente de jogos da sua biblioteca que você ainda não jogou para vencer o backlog.
- ⏱️ **Playtime Tracker:** Monitoramento em tempo real da duração de sessões e estatísticas de horas jogadas por título.
- ⚡ **Downloader Multi-Chunk Paralelo:** Aceleração com múltiplos fluxos simultâneos (HTTP Range) e fallback seguro com barra de progresso.
- 📦 **Extração Automática:** Descompacta automaticamente arquivos `.zip`, `.7z` e `.rar` logo após o download.
- 💿 **Instalador Oficial Windows Standalone (`EmuCraft-Setup.exe`):** Assistente de instalação completo em 4 passos com atalhos e desinstalador registrado no Windows.
- 🧠 **Arquitetura .brain:** Sistema de documentação viva, decisões arquiteturais (ADRs), padrões de engenharia e memória persistente do projeto.

---

## 🕹️ Plataformas Suportadas

| Fabricante | Plataformas Suportadas |
|---|---|
| **Nintendo** | Switch, Switch Ports (Homebrew), NES, SNES, N64, Game Boy (GB), Game Boy Color (GBC), Game Boy Advance (GBA), Nintendo DS (NDS), Nintendo 3DS, GameCube (GC), Wii |
| **PlayStation** | PS1 (PSX), PS2, PS3, PS4, PS5, PSP, PS Vita (PSV) |
| **Microsoft** | Xbox Clássico (OG / XISO), Xbox 360 (XEX), Xbox Live Arcade (XBLA) |
| **Sega & Outros** | Mega Drive / Genesis, Master System, Dreamcast, Saturn, Arcade (MAME / Neo Geo), PC |

---

## 🚀 Como Usar

### 1. Aplicativo Desktop com Interface Gráfica (GUI)

Abra pelo atalho na Área de Trabalho ou execute:
```bash
emucraft --gui       # ou: rom --gui
```

#### Recursos da GUI:
- **Hero Spotlight Banner:** Destaque dinâmico widescreen do último jogo jogado com cover oficial e lançamento imediato.
- **Filtros Rápidos (Pills):** Cápsulas horizontais de seleção de console (Todos, Switch, PS2, Xbox, Xbox 360, etc.).
- **Modo Grade (⊞) & Lista (☰):** Alterne visualização entre posters/capas oficiais ou lista detalhada com estatísticas de tempo de jogo.
- **Roleta Gamer (🎲):** Clique no botão da roleta para sortear um jogo aleatório do seu acervo.
- **Centro de Download:** Busca online instantânea integrada em múltiplos provedores preservados (Myrient, Internet Archive, Sony CDN, Dlpsgame).
- **Gerenciador de Emuladores:** Detecção automática e vinculação de executáveis personalizados (Ryujinx, PCSX2, DuckStation, RPCS3, Dolphin, xemu, Xenia, RetroArch).

---

### 2. Interface Interativa de Terminal (TUI)

```bash
emucraft                 # Abre a TUI interativa de busca online (ou: rom)
emucraft --launch        # Abre a TUI de navegação e lançamento da biblioteca local
```

---

### 3. Linha de Comando (CLI Scriptável)

```bash
# Busca focada em SNES
rom -p snes "metroid"

# Baixa o melhor resultado, extrai o ZIP e lança no emulador configurado direto!
rom -y -x --play -p ps2 "god of war"

# Busca no acervo do Xbox Clássico e Xbox 360
rom -p xbox "halo"
rom -p xbox360 "gears of war"

# Audita se as BIOS e Firmwares dos emuladores estão instalados corretamente
rom --check-bios

# Aplica patch de tradução (IPS ou BPS) diretamente na ROM
rom --patch "Super Mario World.sfc" "traducao_ptbr.ips"

# Lista snapshots de backup de saves e memory cards
rom --backups

# Sorteia um jogo aleatório via Roleta Gamer no terminal
rom --random
rom --random -p snes

# Lista jogos instalados na sua biblioteca local com estatísticas
rom --installed

# Configura o caminho do emulador portátil
rom --set-emulator ps2 "D:\Emuladores\pcsx2.exe"

# Lista todas as plataformas suportadas
rom -l

# Reconstrói caches locais e limpa arquivos temporários
rom --refresh
```

---

## 📦 Instalação & Compilação

> [!NOTE]
> **Aviso sobre o Google Chrome e Windows SmartScreen:**  
> Por ser um projeto de código aberto recém-lançado no GitHub e sem certificado comercial pago (EV Authenticode de \$400/ano), o Google Safe Browsing e o Windows SmartScreen podem emitir um alerta preventivo de "Download não verificado / Arquivo suspeito":
> - **No Chrome:** Abra o histórico de downloads (`Ctrl + J`) e selecione **"Manter arquivo suspeito"** / **"Manter mesmo assim"**.
> - **No Windows:** Na janela azul *"O Windows protegeu o seu computador"*, clique em **"Mais informações"** e depois em **"Executar assim mesmo"**.
> - **Formato Portátil Recomendado:** Se preferir, baixe o pacote **`EmuCraft-Portable.zip`** na aba de Releases, descompacte em qualquer pasta e execute sem nenhum bloqueio.

### Opção A: Instalador Oficial Windows (`EmuCraft-Setup.exe`)
Gera o instalador padrão do Windows via Inno Setup com desinstalador registrado no Painel de Controle:
```powershell
powershell -ExecutionPolicy Bypass -File .\build-setup.ps1
```

### Opção B: Compilar Executável Portátil Standalone (.exe)
Gera `dist\EmuCraft.exe` com metadados PE oficiais do Windows e sem compressão UPX:
```powershell
powershell -ExecutionPolicy Bypass -File .\build-exe.ps1
```

### Opção C: Instalação via Python pip (Cross-Platform)
```bash
git clone https://github.com/Henrique1601/rom-launcher.git
cd rom-launcher
pip install -e .[full]
```

---

## 🧪 Suíte de Testes Automatizados

O projeto conta com cobertura completa de testes unitários:

```bash
python -m unittest discover tests
```

- `test_validator.py`: Validação de cabeçalhos e magic bytes (`PFS0`, `PKG`, `XBEH`, `XEX2`, `PK`, `7z`).
- `test_extractor.py`: Descompactação de arquivos `.zip`, `.7z` e `.rar`.
- `test_launcher.py`: Localização de executáveis e montagem de comandos de emulador.
- `test_tracker.py`: Cálculo de duração de sessões e persistência de playtime.
- `test_retroachievements.py`: Conexão com API e tratamento de erros de rede.
- `test_roulette.py`: Algoritmo de sorteio com priorização de títulos não jogados.
- `test_gamepad.py`: Emulação e estrutura de estados dos botões XInput.
- `test_savesync.py`: Snapshots automáticos de saves e memory cards de emuladores.
- `test_patcher.py`: Aplicação de patches de tradução IPS e BPS.
- `test_bios_checker.py`: Auditoria de regras e presença de firmwares de emuladores.
- `test_installer_and_gui.py`: Validação de tokens Liquid Glass e geração de atalhos/desinstalador do assistente.
- `test_utils.py`: Sanitização de nomes de arquivos e fallback para codificação `cp1252` no Windows.

---

## 🏛️ Arquitetura do Repositório

```
emucraft/
├── .brain/                     # Memória persistente, ADRs e padrões de engenharia
├── .github/workflows/          # Automação CI (testes) e Release (build de binários)
├── build-exe.ps1               # Compilador Standalone PyInstaller
├── build-setup.ps1             # Compilador de Setup Inno Setup
├── install-desktop.ps1         # Instalador de atalhos silenciosos para Windows
├── installer.iss               # Script Inno Setup Compiler
├── pyproject.toml              # Metadados do pacote Python
├── src/rom_cli/
│   ├── config.py               # Configurações globais e paths cross-platform
│   ├── models.py               # Dataclass RomItem
│   ├── main.py                 # CLI, parser de argumentos e roteamento
│   ├── core/
│   │   ├── downloader.py       # Motor multi-chunk HTTP Range paralelo
│   │   ├── extractor.py        # Extração automática (.zip, .7z, .rar)
│   │   ├── gamepad.py          # Listener XInput de controles de videogame
│   │   ├── launcher.py         # Monitor de processos de emuladores
│   │   ├── ranking.py          # Algoritmo de busca e relevância Wikipedia
│   │   ├── retroachievements.py# Integração oficial com RetroAchievements
│   │   ├── roulette.py         # Sorteador inteligente de backlog
│   │   ├── scraper.py          # Box art scraper (Libretro Thumbnails)
│   │   ├── tracker.py          # Rastreador de tempo de jogo
│   │   ├── validator.py        # Verificador de integridade de arquivos
│   │   └── utils.py            # Utilitários seguros de string e I/O
│   ├── providers/              # Provedores modulares de acervos de ROMs
│   ├── launcher/               # Scanner de biblioteca e TUI
│   └── gui/                    # Interface gráfica desktop CustomTkinter
└── tests/                      # Suíte de testes unitários automatizados
```

---

## ⚖️ Aviso Legal

Este software foi desenvolvido exclusivamente para fins educacionais, de pesquisa, interoperabilidade e preservação histórica de mídias legalmente adquiridas pelo usuário. Os autores não hospedam nem distribuem arquivos protegidos por direitos autorais.
