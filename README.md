# ROM Launcher & Downloader (rom-cli)

Plataforma completa de preservação, download e inicialização de jogos retrô e modernos para Windows, Linux e macOS. Inclui aplicativo desktop com interface gráfica moderna (**CustomTkinter**), interface de terminal (**Textual TUI**) e CLI rápida e scriptável.

---

## 🎮 Plataformas Suportadas

- **Nintendo:** Switch, Switch Ports (Homebrew), NES, SNES, N64, Game Boy (GB), Game Boy Color (GBC), Game Boy Advance (GBA), Nintendo DS (NDS), Nintendo 3DS, GameCube (GC), Wii.
- **PlayStation:** PS1, PS2, PS3, PS4, PS5, PSP, PS Vita (PSV).
- **Microsoft Xbox:** Xbox Clássico (OG), Xbox 360, Xbox Live Arcade (XBLA).
- **Sega & Outros:** Sega Genesis / Mega Drive, Master System, Dreamcast, Saturn, Arcade (MAME / Neo Geo) e PC.

---

## 🚀 Como Usar o Aplicativo

### 1. Aplicativo Desktop com Interface Gráfica (Estilo Playnite / RetroArch)
Você pode abrir o aplicativo desktop nativo:
- Dando dois cliques no atalho **ROM Launcher** na sua Área de Trabalho ou Menu Iniciar.
- Ou via comando:
  ```bash
  rom --gui
  ```

#### Recursos da Interface Gráfica:
- **Modo Grade com Capas Oficiais (Box Art):** Baixa posters automaticamente via Libretro Thumbnails.
- **Rastreador de Horas (Playtime Tracker):** Monitora a duração das sessões e tempo total jogado por jogo.
- **Filtros e Ordenação:** Ordene por Nome, Mais Jogados, Jogados Recentemente ou Tamanho.
- **Download Center:** Busca online integrada em provedores preservados (Myrient, Sony CDN, Archive.org, dlarchive).
- **Configurador de Emuladores:** Localiza ou associa arquivos `.exe` personalizados para seus emuladores (Ryujinx, PCSX2, DuckStation, RPCS3, Dolphin, xemu, Xenia, RetroArch).

---

### 2. Interface Terminal Interativa (TUI)
```bash
rom                     # Abre a TUI interativa de busca online
rom --launch            # Abre a TUI de gerenciamento da sua biblioteca local de jogos
```

---

### 3. Comandos Rápidos de Terminal (CLI)
```bash
rom -p snes "metroid"                  # Busca focada em SNES
rom -y -x --play -p ps2 "god of war"   # Baixa o melhor, extrai zip e abre no emulador direto!
rom -p xbox "halo"                     # Busca no acervo de Xbox Clássico
rom -p xbox360 "gears"                 # Busca no acervo de Xbox 360
rom --installed                        # Lista todos os jogos já baixados na máquina
rom --set-emulator ps2 "D:\pcsx2.exe"  # Define o caminho de um emulador portátil
rom -l                                 # Lista todas as plataformas disponíveis
rom --refresh                          # Reconstrói os índices e caches
```

---

## 📦 Instalação & Compilação

### Instalador Desktop para Windows (Cria atalhos na Área de Trabalho e Menu Iniciar):
```powershell
powershell -ExecutionPolicy Bypass -File .\install-desktop.ps1
```

### Compilar Executável Único Standalone (.exe portátil sem precisar de Python):
```powershell
powershell -ExecutionPolicy Bypass -File .\build-exe.ps1
```
> O arquivo `dist\ROM-Launcher.exe` gerado roda em qualquer PC com Windows sem necessidade de Python instalado.

### Instalação no Linux / macOS:
```bash
chmod +x ./install.sh
./install.sh
```

---

## 🏛️ Arquitetura do Projeto

```
rom/
├── install-desktop.ps1         # Instalador Desktop com atalhos Windows
├── build-exe.ps1               # Compilador Standalone .exe com PyInstaller
├── install.ps1                 # Instalador CLI Windows
├── install.sh                  # Instalador Unix
├── pyproject.toml              # Metadados e dependências
├── src/rom_cli/
│   ├── config.py               # Configurações globais e paths cross-platform
│   ├── models.py               # Modelos e Dataclasses
│   ├── main.py                 # Ponto de entrada CLI e roteamento
│   ├── core/
│   │   ├── downloader.py       # Motor multi-chunk paralelo com HTTP Range
│   │   ├── extractor.py        # Extração automática (.zip, .7z, .rar)
│   │   ├── launcher.py         # Lançador e monitor de processos de emuladores
│   │   ├── scraper.py          # Scraper de capas oficiais (Libretro Thumbnails)
│   │   ├── tracker.py          # Rastreador de tempo jogado e estatísticas
│   │   ├── ranking.py          # Algoritmo de relevância e popularidade Wikipedia
│   │   ├── validator.py        # Validação de integridade e magic bytes (PFS0, PKG, XBE, XEX)
│   │   └── utils.py            # Utilitários HTTP, codificação e strings
│   ├── providers/              # Provedores modulares
│   │   ├── myrient.py          # Acervo No-Intro e Redump do Myrient
│   │   ├── archive_org.py      # Internet Archive (Xbox, Redump, Ports)
│   │   ├── dlarchive.py        # API do DlArchive (Switch, PC, NDS, etc.)
│   │   ├── nopaystation.py     # CDN oficial da Sony (PS3, Vita, PSP)
│   │   ├── dlpsgame.py         # Dlpsgame (PS4, PS5)
│   │   └── romsgames.py        # RomsGames
│   ├── launcher/               # Módulos do Launcher de Jogos
│   │   ├── scanner.py          # Scanner de ROMs locais na biblioteca
│   │   ├── registry.py         # Registro e detecção de emuladores locais
│   │   └── tui_launcher.py     # Launcher em modo terminal (Textual)
│   └── gui/                    # Aplicativo Desktop Nativo (CustomTkinter)
│       └── main_window.py      # Janela principal com biblioteca, capas e loja
└── tests/                      # Suíte de testes unitários automatizados
```

---

## ⚖️ Aviso Legal

Este software foi desenvolvido exclusivamente para fins de pesquisa, automação e preservação de mídias que você legalmente possua. Use com responsabilidade.
