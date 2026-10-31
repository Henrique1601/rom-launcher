# Compilador do Instalador Standalone Oficial (ROM-Launcher-Setup.exe)
$ErrorActionPreference = "Stop"

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   Compilando Instalador ROM-Launcher-Setup.exe  " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

$ProjectDir = $PSScriptRoot
$PythonExe = (Get-Command python.exe).Source
$SetupEntry = Join-Path $ProjectDir "src\rom_cli\installer\setup_wizard.py"
$DistDir = Join-Path $ProjectDir "dist"
$BuildDir = Join-Path $ProjectDir "build\setup"

# 1. Compila o aplicativo principal atualizado em dist\ROM-Launcher.exe
$MainExe = Join-Path $DistDir "ROM-Launcher.exe"
Write-Host "[1/2] Compilando executavel principal atualizado..." -ForegroundColor Yellow
& (Join-Path $ProjectDir "build-exe.ps1")

# 2. Compila o Instalador Standalone
Write-Host "[2/2] Compilando assistente de instalacao com PyInstaller..." -ForegroundColor Yellow

& $PythonExe -m PyInstaller `
    --name "ROM-Launcher-Setup" `
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
Write-Host "Arquivo gerado em: $DistDir\ROM-Launcher-Setup.exe" -ForegroundColor White
Write-Host "Este arquivo eh o instalador completo oficial que voce pode distribuir e instalar em qualquer computador Windows!" -ForegroundColor Cyan
