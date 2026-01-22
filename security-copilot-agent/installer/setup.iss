; Script de Inno Setup para Galt.ai - "Traditional Setup"
; Documentación: https://jrsoftware.org/ishelp/

#define MyAppName "Galt.ai Security Suite"
#define MyAppVersion "3.0"
#define MyAppPublisher "Galt.ai Security Division"
#define MyAppURL "https://galt.ai"
#define MyAppExeName "GaltAI_Agent.exe"

[Setup]
; ID Único de la aplicación (No cambiar para actualizaciones)
AppId={{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
; Directorio por defecto: C:\Program Files\Galt.ai Security Suite
DefaultDirName={autopf}\{#MyAppName}
; Nombre del grupo en Menú Inicio
DefaultGroupName={#MyAppName}
; Requerir Admin para instalación y ejecución (Vital para ciberseguridad)
PrivilegesRequired=admin
; Ruta de salida del instalador
OutputDir=..\release
OutputBaseFilename=GaltAI_Setup_Windows
; Icono del instalador (si tienes uno, sino comentar)
; SetupIconFile=..\app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; MOSTRAR LICENCIA "ACEPTO"
LicenseFile=..\license.txt
; Mostrar página de "Información antes de instalar" (opcional)
; InfoBeforeFile=..\README.txt

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
; Checkbox opcional para icono en escritorio
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
; Checkbox para iniciar con Windows (Marcado por defecto)
Name: "autostart"; Description: "Iniciar Galt.ai automáticamente con Windows (Recomendado para monitoreo 24/7)"; GroupDescription: "Configuración de Servicio:"; Flags: checkedonce

[Files]
; El ejecutable principal compilado
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Archivo de ejemplo .env
Source: "..\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: skipifsourcedoesnexist onlyifdoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; CONFIGURACIÓN DE AUTO-ARRANQUE
; Escribe en HKLM (Machine) para que arranque para todos los usuarios o HKCU (Current User)
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "GaltAI_Sentinel"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
; Ejecutar al finalizar la instalación
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait
