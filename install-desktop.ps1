# Instalador do ROM Launcher Desktop para Windows.
$ErrorActionPreference = "Stop"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "     Instalador do ROM Launcher Desktop      " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$ProjectDir = $PSScriptRoot
$SrcDir = Join-Path $ProjectDir "src"
$PythonExe = (Get-Command python.exe).Source
$PythonwExe = $PythonExe -replace "python\.exe$", "pythonw.exe"

if (-not (Test-Path $PythonwExe)) {
    $PythonwExe = $PythonExe
}

Write-Host "[1/4] Verificando dependencias graficas (CustomTkinter, Pillow)..." -ForegroundColor Yellow
& $PythonExe -m pip install --upgrade customtkinter pillow

Write-Host "[2/4] Criando script de inicializacao do Desktop..." -ForegroundColor Yellow
$BinDir = Join-Path $HOME "AppData\Local\Programs\ROMLauncher"
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
}

$LaunchVbs = Join-Path $BinDir "LaunchROMLauncher.vbs"
$VbsContent = "Set WshShell = CreateObject(`"WScript.Shell`")`nWshShell.CurrentDirectory = `"$ProjectDir`"`nWshShell.Environment(`"PROCESS`")(`"PYTHONPATH`") = `"$SrcDir`"`nWshShell.Run `"`"`"$PythonwExe`"`" -m rom_cli.gui.main_window`", 0, False"
Set-Content -Path $LaunchVbs -Value $VbsContent -Encoding ASCII

Write-Host "[3/4] Criando atalho na Area de Trabalho (Desktop)..." -ForegroundColor Yellow
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$DesktopShortcutPath = Join-Path $DesktopPath "ROM Launcher.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($DesktopShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$LaunchVbs`""
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "ROM Launcher - Central de Emulacao e Preservacao de Jogos"
$Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,24"
$Shortcut.Save()

Write-Host "[4/4] Criando atalho no Menu Iniciar..." -ForegroundColor Yellow
$StartMenuPrograms = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Programs)
$StartMenuShortcutPath = Join-Path $StartMenuPrograms "ROM Launcher.lnk"

$StartShortcut = $WshShell.CreateShortcut($StartMenuShortcutPath)
$StartShortcut.TargetPath = "wscript.exe"
$StartShortcut.Arguments = "`"$LaunchVbs`""
$StartShortcut.WorkingDirectory = $ProjectDir
$StartShortcut.Description = "ROM Launcher - Central de Emulacao e Preservacao de Jogos"
$StartShortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,24"
$StartShortcut.Save()

Write-Host ""
Write-Host "INSTALACAO CONCLUIDA COM SUCESSO!" -ForegroundColor Green
Write-Host "-> Atalho na Area de Trabalho: $DesktopShortcutPath" -ForegroundColor White
Write-Host "-> Atalho no Menu Iniciar:     $StartMenuShortcutPath" -ForegroundColor White
Write-Host ""
Write-Host "Abra o ROM Launcher dando dois cliques no icone da sua Area de Trabalho!" -ForegroundColor Cyan
