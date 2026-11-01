; Matick Studio LM Cloud - instalador independiente por usuario, Windows x64.
; El script compilador Inno Setup SOLO se utiliza en CI, no se instala en el PC.
#define BundleRoot GetEnv("MATICK_PACKAGE_DIR")
#if BundleRoot == ""
  #error "Primero establece MATICK_PACKAGE_DIR al paquete previamente verificado."
#endif
#define MyAppVersion "1.0.1"

[Setup]
AppId={{D3A69EE0-6D63-4326-9B45-723A00DCA110}
AppName=Matick Studio LM Cloud
AppVersion={#MyAppVersion}
AppVerName=Matick Studio LM Cloud {#MyAppVersion}
AppPublisher=Matick Project
AppPublisherURL=https://github.com/DannMorlet/IA-Local-Cursor
AppSupportURL=https://github.com/DannMorlet/IA-Local-Cursor/issues
AppUpdatesURL=https://github.com/DannMorlet/IA-Local-Cursor/releases
DefaultDirName={localappdata}\Programs\Matick Studio LM Cloud
DefaultGroupName=Matick Studio LM Cloud
DisableDirPage=yes
DisableProgramGroupPage=yes
UsePreviousAppDir=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Uninstallable=yes
UninstallDisplayIcon={app}\MatickStudioLM.exe
UninstallDisplayName=Matick Studio LM Cloud
Compression=lzma2
SolidCompression=yes
SetupLogging=yes
WizardStyle=modern
ChangesAssociations=no
CloseApplications=yes
RestartApplications=no
CreateUninstallRegKey=yes
OutputDir=.
OutputBaseFilename=MatickStudioLM-v1.0.1-x64-Setup
DisableWelcomePage=no
DisableReadyPage=no
DisableFinishedPage=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
; Solo el directorio empaquetado por lista blanca y con SHA256. Sin modelos ni CUDA.
Source: "{#BundleRoot}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Matick Studio LM Cloud"; Filename: "{app}\MatickStudioLM.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Matick Studio LM Cloud"; Filename: "{app}\MatickStudioLM.exe"; Tasks: desktopicon; WorkingDir: "{app}"

[Run]
Filename: "{app}\MatickStudioLM.exe"; Description: "Abrir Matick Studio LM"; Flags: nowait postinstall skipifsilent

; IMPORTANTE: No hay [UninstallDelete]. Los datos propios del usuario se
; guardan en %LOCALAPPDATA%\MatickStudioLM y se CONSERVAN tras desinstalar.
; No se tocan C:\IA\Matick Studio LM, modelos, proyectos ni apps externas.
