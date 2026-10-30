# Compilador de Instalador Profissional (ROM-Launcher-Setup.exe)
$ErrorActionPreference = "Stop"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Compilador de Setup Oficial (Inno Setup)  " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$ProjectDir = $PSScriptRoot
$ExePath = Join-Path $ProjectDir "dist\ROM-Launcher.exe"

# 1. Verifica se o executavel base já foi compilado
if (-not (Test-Path $ExePath)) {
    Write-Host "[1/2] Compilando executavel base ROM-Launcher.exe..." -ForegroundColor Yellow
    & "$ProjectDir\build-exe.ps1"
} else {
    Write-Host "[1/2] Executavel base ROM-Launcher.exe encontrado em dist/." -ForegroundColor Green
}

# 2. Localiza o compilador do Inno Setup (iscc.exe)
$InnoPath = $null
$CommonInnoPaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)

foreach ($path in $CommonInnoPaths) {
    if (Test-Path $path) {
        $InnoPath = $path
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
    Write-Host "✔ INSTALADOR CRIADO COM SUCESSO!" -ForegroundColor Green
    Write-Host "Arquivo gerado: $ProjectDir\dist\ROM-Launcher-Setup.exe" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "AVISO: Inno Setup 6 não encontrado no PATH." -ForegroundColor Yellow
    Write-Host "Para gerar o arquivo 'ROM-Launcher-Setup.exe':" -ForegroundColor White
    Write-Host "1. Instale o Inno Setup via winget:" -ForegroundColor Cyan
    Write-Host "   winget install JRSoftware.InnoSetup" -ForegroundColor White
    Write-Host "2. Em seguida, execute este script novamente:" -ForegroundColor Cyan
    Write-Host "   .\build-setup.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "O script 'installer.iss' já está 100% pronto e configurado no repositório." -ForegroundColor Green
}
