# Instalação do rom-cli no Windows (PowerShell)

$VenvPath = Join-Path $HOME ".venvs\rom"
$BinDir = Join-Path $HOME "bin"

Write-Host "Criando ambiente virtual em $VenvPath..." -ForegroundColor Cyan
if (-not (Test-Path $VenvPath)) {
    python -m venv $VenvPath
}

$PipPath = Join-Path $VenvPath "Scripts\pip.exe"
$PythonPath = Join-Path $VenvPath "Scripts\python.exe"

Write-Host "Instalando dependências e o rom-cli..." -ForegroundColor Cyan
& $PipPath install --upgrade pip
& $PipPath install -e .

if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
}

$ShimPath = Join-Path $BinDir "rom.cmd"
"@echo off
`"$PythonPath`" -m rom_cli.main %*
" | Set-Content -Path $ShimPath -Encoding ASCII

Write-Host "Instalação concluída com sucesso!" -ForegroundColor Green
Write-Host "Comando disponível em: $ShimPath" -ForegroundColor Green
Write-Host "Certifique-se de que '$BinDir' está no seu PATH do sistema." -ForegroundColor Yellow
