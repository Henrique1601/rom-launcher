# Compilador do Instalador Standalone Oficial (EmuCraft-Setup.exe)
$ErrorActionPreference = "Stop"

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "     Compilando Instalador EmuCraft-Setup.exe    " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

$ProjectDir = $PSScriptRoot
$PythonExe = (Get-Command python.exe).Source
$SetupEntry = Join-Path $ProjectDir "src\rom_cli\installer\setup_wizard.py"
$DistDir = Join-Path $ProjectDir "dist"
$BuildDir = Join-Path $ProjectDir "build\setup"

# 1. Compila o aplicativo principal atualizado em dist\EmuCraft.exe
$MainExe = Join-Path $DistDir "EmuCraft.exe"
Write-Host "[1/2] Compilando executavel principal atualizado..." -ForegroundColor Yellow
& (Join-Path $ProjectDir "build-exe.ps1")

# 2. Compila o Instalador Standalone
Write-Host "[2/2] Compilando assistente de instalacao com PyInstaller..." -ForegroundColor Yellow

& $PythonExe -m PyInstaller `
    --name "EmuCraft-Setup" `
    --noconsole `
    --onefile `
    --paths "src" `
    --add-data "$MainExe;payload" `
    --collect-all "customtkinter" `
    --hidden-import "PIL" `
    --distpath "$DistDir" `
    --workpath "$BuildDir" `
    --clean `
    -y `
    "$SetupEntry"

Write-Host ""
Write-Host "[OK] INSTALADOR STANDALONE COMPILADO COM SUCESSO!" -ForegroundColor Green
Write-Host "Arquivo gerado em: $DistDir\EmuCraft-Setup.exe" -ForegroundColor White
Write-Host "Este arquivo eh o instalador completo oficial do EmuCraft que voce pode distribuir e instalar em qualquer computador Windows!" -ForegroundColor Cyan
