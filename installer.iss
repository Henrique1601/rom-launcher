; Script de Instalador Inno Setup para o EmuCraft Desktop
; Baixe o Inno Setup gratuitamente em: https://jrsoftware.org/isdl.php

#define MyAppName "EmuCraft"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "EmuCraft Community"
#define MyAppURL "https://github.com/Henrique1601/emucraft"
#define MyAppExeName "EmuCraft.exe"

[Setup]
AppId={{9B7D25E4-7E2A-4C26-8B2A-2D8F8F9B6E1A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=EmuCraft-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Inclui o executavel compilado da pasta dist
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Se houver outros arquivos necessarios, copie para {app}

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
