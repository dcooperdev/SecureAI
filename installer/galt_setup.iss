; installer/galt_setup.iss
#define MyAppName "Galt.ai Security Suite"
#define MyAppVersion "3.0.3"
#define MyAppPublisher "Galt.ai Security Division"
#define MyAppExeName "GaltAI_Agent.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
PrivilegesRequired=admin
OutputDir=..\Output
OutputBaseFilename=GaltAI_Setup_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
; Nota: En GitHub Actions, el ejecutable se genera en la raíz o dist. 
; Asegúrate de que build_windows.py lo deje donde Inno Setup lo busca.
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: skipifsourcedoesnexist onlyifdoesntexist

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Galt.ai"; Flags: nowait postinstall skipifsilent