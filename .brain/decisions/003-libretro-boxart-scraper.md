# ADR 003: Uso do Libretro Thumbnails como Fonte Aberta de Capas

## Contexto
Para exibir posters/capas 2D na visualização em Grade da biblioteca, precisávamos de uma base de imagens com alta cobertura de títulos retrô.
APIs como IGDB ou SteamGridDB exigem chaves de API pagas, registro OAuth de desenvolvedor ou aprovação de conta.

## Decisão
Integrar o repositório aberto **Libretro Thumbnails** (`raw.githubusercontent.com/libretro-thumbnails/`):
- Totalmente gratuito e sem rate-limits agressivos para consulta direta de arquivos brutos.
- Padronizado exatamente pelos nomes das ROMs dos conjuntos No-Intro e Redump.
- Implementação de cache em disco local em `%LOCALAPPDATA%\rom-cli\covers\<plataforma>\<jogo>.png`.

## Consequências
- A experiência "out-of-the-box" do usuário funciona imediatamente sem requerer cadastro ou chaves de API.
- Imagens são baixadas assincronamente e salvas em disco, garantindo que consultas subsequentes sejam instantâneas.
