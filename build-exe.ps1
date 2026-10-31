# Compilador de Executavel Standalone (.exe) para o EmuCraft Desktop
$ErrorActionPreference = "Stop"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "    Compilando EmuCraft.exe com PyInstaller  " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$ProjectDir = $PSScriptRoot
$PythonExe = (Get-Command python.exe).Source

Write-Host "[1/3] Verificando instalacao do PyInstaller..." -ForegroundColor Yellow
& $PythonExe -m pip install --upgrade pyinstaller

Write-Host "[2/3] Compilando executavel nativo do Windows..." -ForegroundColor Yellow
$EntryFile = Join-Path $ProjectDir "src\rom_cli\gui\main_window.py"
$DistDir = Join-Path $ProjectDir "dist"
$BuildDir = Join-Path $ProjectDir "build"

& $PythonExe -m PyInstaller `
    --name "EmuCraft" `
    --noconsole `
    --onefile `
    --paths "src" `
    --collect-all "customtkinter" `
    --hidden-import "PIL" `
    --hidden-import "rom_cli" `
    --distpath "$DistDir" `
    --workpath "$BuildDir" `
    --clean `
    -y `
    "$EntryFile"

Write-Host ""
Write-Host "[3/3] Compilacao concluida!" -ForegroundColor Green
Write-Host "Executavel gerado em: $DistDir\EmuCraft.exe" -ForegroundColor White
Write-Host "Voce pode executar esse arquivo diretamente ou move-lo para qualquer pasta/PC sem precisar do Python!" -ForegroundColor Cyan
