; Script generado para Inno Setup
; Requiere Inno Setup instalado en la PC de compilación

#define MyAppName "Galt.ai Security Suite"
#define MyAppVersion "2.0"
#define MyAppPublisher "Galt.ai Inc."
#define MyAppURL "https://galt.ai"
#define MyAppExeName "GaltAI_Agent.exe"

[Setup]
; Identificador único (Generar uno nuevo en Inno Setup tools -> Generate GUID)
AppId={{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Pedir admin para poder escanear puertos y procesos
PrivilegesRequired=admin
OutputDir=..\release
OutputBaseFilename=GaltAI_Setup_Windows
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; El ejecutable compilado por PyInstaller
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
