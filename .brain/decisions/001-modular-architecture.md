# ADR 001: Modularização da Base de Código (Extinção do Monólito)

## Contexto
O repositório original clonado (`rom-cli-main`) consistia em um único arquivo script de ~1.800 linhas em `bin/rom`, fortemente amarrado a caminhos Unix (`~/.venvs/rom` e links em `~/bin`).

## Decisão
Desmembrar o monólito em pacotes especializados sob `src/rom_cli/`:
- `core/`: Utilitários fundamentais, downloaders, validação, ranking e rastreamento.
- `providers/`: Adaptadores isolados para cada fonte (Myrient, Archive.org, dlarchive, Sony CDN, etc.) herdando de `BaseProvider`.
- `launcher/`: Varredura local, registro de emuladores e TUI de lançamento.
- `gui/`: Janela gráfica desktop em CustomTkinter.

## Consequências
- Código altamente testável e manutenível.
- Adicionar um novo console ou provedor requer apenas criar um novo arquivo em `providers/` sem tocar no restante do sistema.
