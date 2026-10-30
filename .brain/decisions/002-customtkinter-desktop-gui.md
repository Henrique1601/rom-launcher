# ADR 002: Adoção do CustomTkinter para Interface Gráfica Desktop

## Contexto
O usuário solicitou um launcher instalável no estilo de RetroArch e Playnite (janela desktop moderna com tema escuro, botões, cards e visualização sem linha de comando).
O ambiente utiliza Python 3.14 no Windows, versão que não possui binários pré-compilados estáveis de bibliotecas C pesadas como PyQt6 ou Flet no momento da implementação.

## Decisão
Utilizar o **CustomTkinter** com **Pillow (PIL)**:
- Roda sobre o `tkinter` nativo já embutido no Python do Windows.
- Entrega visual moderno em Dark Mode com widgets arredondados, segmented buttons, barras de progresso e scroll frames responsivos.
- Suporta empacotamento standalone direto com PyInstaller (`build-exe.ps1`) com footprint leve (~35MB a 45MB).

## Consequências
- Zero complexidade de drivers externos.
- Inicialização ultra-rápida (< 1 segundo).
- Experiência visual nativa comparável a aplicativos comerciais.
