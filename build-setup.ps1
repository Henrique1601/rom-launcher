# Script de compilacao do Instalador Oficial Inno Setup
$ErrorActionPreference = "Stop"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Criando Instalador ROM-Launcher-Setup.exe  " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$ProjectDir = $PSScriptRoot
$DistExe = Join-Path $ProjectDir "dist\ROM-Launcher.exe"

# 1. Garante que o executavel standalone existe
if (-not (Test-Path $DistExe)) {
    Write-Host "[1/2] Executavel dist\ROM-Launcher.exe nao encontrado. Compilando com PyInstaller..." -ForegroundColor Yellow
    & (Join-Path $ProjectDir "build-exe.ps1")
} else {
    Write-Host "[1/2] Executavel dist\ROM-Launcher.exe pronto." -ForegroundColor Green
}

# 2. Localiza o compilador do Inno Setup (ISCC.exe)
$InnoPath = $null
$CommonPaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    "C:\Program Files\Inno Setup 5\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)

foreach ($p in $CommonPaths) {
    if (Test-Path $p) {
        $InnoPath = $p
        break
    }
}

if (-not $InnoPath) {
    $whichIscc = Get-Command "iscc.exe" -ErrorAction SilentlyContinue
    if ($whichIscc) {
        $InnoPath = $whichIscc.Source
    }
}

if ($InnoPath) {
    Write-Host "[2/2] Compilando instalador com Inno Setup ($InnoPath)..." -ForegroundColor Yellow
    & $InnoPath (Join-Path $ProjectDir "installer.iss")
    Write-Host ""
    Write-Host "[OK] INSTALADOR CRIADO COM SUCESSO!" -ForegroundColor Green
    Write-Host "Arquivo gerado: $ProjectDir\dist\ROM-Launcher-Setup.exe" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "AVISO: Inno Setup 6 nao encontrado no PATH." -ForegroundColor Yellow
    Write-Host "Para gerar o arquivo 'ROM-Launcher-Setup.exe':" -ForegroundColor White
    Write-Host "1. Instale o Inno Setup via winget:" -ForegroundColor Cyan
    Write-Host "   winget install JRSoftware.InnoSetup" -ForegroundColor White
    Write-Host "2. Em seguida, execute este script novamente:" -ForegroundColor Cyan
    Write-Host "   .\build-setup.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "O script 'installer.iss' ja esta 100% pronto e configurado no repositorio." -ForegroundColor Green
}
