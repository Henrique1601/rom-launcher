# rom-cli

CLI em Python para encontrar e baixar ROMs, ISOs e jogos diretamente pelo terminal, com interface interativa TUI (Textual), organização automática e suporte completo multiplataforma (**Windows**, **Linux** e **macOS**).

---

## 🎮 Plataformas Suportadas

- **Nintendo:** Switch, Switch Ports (Homebrews), NES, SNES, N64, Game Boy (GB), Game Boy Color (GBC), Game Boy Advance (GBA), Nintendo DS (NDS), Nintendo 3DS, GameCube (GC), Wii.
- **PlayStation:** PS1, PS2, PS3, PS4, PS5, PSP, PS Vita (PSV).
- **Sega & Outros:** Sega Genesis / Mega Drive, Master System, Dreamcast, Saturn, Arcade (MAME / Neo Geo) e PC.

---

## 📦 Instalação

### No Windows (PowerShell):
```powershell
.\install.ps1
```
> O script cria o venv em `%USERPROFILE%\.venvs\rom` e gera o executável `rom.cmd` em `%USERPROFILE%\bin`. Certifique-se de que essa pasta esteja no seu `PATH`.

### No Linux / macOS:
```bash
chmod +x ./install.sh
./install.sh
```

### Instalação Manual (Pip / Venv):
```bash
python -m pip install -e .
```

---

## 🚀 Como Usar

```bash
rom                          # Abre a TUI interativa com seletor de plataformas
rom -p switch                # Abre a TUI já navegando no catálogo de Switch
rom -p switchports           # Lista apenas ports/homebrew de Switch
rom "zelda"                  # Busca 'zelda' em todas as plataformas
rom -p snes "metroid"        # Busca focada em SNES
rom -y -p gba "pokemon"      # Baixa o melhor resultado sem perguntar
rom --list "mario"           # Apenas lista os resultados no terminal
rom --print-url -p switch …  # Resolve e exibe a URL direta (para curl/aria2)
rom -l                       # Lista todas as plataformas disponíveis
rom --refresh                # Reconstrói os índices e caches
```

---

## 🏛️ Estrutura do Código

```
rom/
├── pyproject.toml              # Metadados e dependências
├── install.ps1                 # Instalador Windows
├── install.sh                  # Instalador Unix
├── src/rom_cli/
│   ├── config.py               # Configurações globais e paths cross-platform
│   ├── models.py               # Modelos e Dataclasses
│   ├── main.py                 # Ponto de entrada CLI
│   ├── core/
│   │   ├── cache.py            # Cache com TTL
│   │   ├── downloader.py       # Motor de download com HTTP Range
│   │   ├── ranking.py          # Ranking e dados populares (Wikipedia)
│   │   ├── utils.py            # Helpers e requisições HTTP
│   │   └── validator.py        # Validação de magic bytes (PFS0, PKG, ZIP, 7z)
│   ├── providers/              # Provedores modulares
│   │   ├── archive_org.py      # Archive.org
│   │   ├── dlarchive.py        # DlArchive API
│   │   ├── dlpsgame.py         # WP REST API
│   │   ├── nopaystation.py     # Sony CDN & NoPayStation
│   │   └── romsgames.py        # RomsGames
│   └── tui/
│       └── app.py              # Interface TUI (Textual)
└── tests/                      # Suíte de testes unitários
```

---

## ⚖️ Aviso Legal

Este software foi desenvolvido exclusivamente para fins de pesquisa, automação e preservação pessoal de mídias que você legalmente possua. Use com responsabilidade.
