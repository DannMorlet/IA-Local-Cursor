# GemCo Joystick - instalador transparente para Windows 11.
# Ejemplo en PowerShell abierto como administrador (por escribir en Program Files):
# .\instalar.ps1 -McpJsonPath "C:\ruta\del\mcp.json" -InstallDependencies -VirtualXbox
param(
  [string]$Destination = "C:\Program Files\LM Studio\Habilidades\GemCo-Joystick",
  [string]$Python = "C:\Python315\python.exe",
  [string]$McpJsonPath = "",
  [switch]$InstallDependencies,
  [switch]$VirtualXbox
)
$ErrorActionPreference="Stop"
if (!(Test-Path -LiteralPath $Python)) { throw "No existe Python en $Python. Pasa -Python con su ruta." }
if (!(Test-Path -LiteralPath (Join-Path $PSScriptRoot "server.py"))) { throw "Ejecuta instalar.ps1 desde su carpeta descargada." }
Write-Host "Destino: $Destination"
Write-Host "Se necesita autorización de Windows para escribir en Program Files."
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
Get-ChildItem -LiteralPath $PSScriptRoot -File | ForEach-Object {
  Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $Destination $_.Name) -Force
}
if ($InstallDependencies) {
  & $Python -m pip install -r (Join-Path $Destination "requirements.txt")
  if ($LASTEXITCODE -ne 0) { throw "No pudieron instalarse las dependencias." }
}
if ($VirtualXbox) {
  Write-Host "vgamepad instala el controlador ViGEmBus, con su consentimiento de Windows."
  & $Python -m pip install vgamepad
  if ($LASTEXITCODE -ne 0) { throw "No se pudo instalar el mando virtual; revisa ViGEmBus." }
}
$entry=[ordered]@{
  command=$Python
  args=@("-X","utf8",(Join-Path $Destination "server.py"))
  cwd=$Destination
  env=@{PYTHONUTF8="1"}
}
if ($McpJsonPath) {
  if (!(Test-Path -LiteralPath $McpJsonPath)) { throw "No existe mcp.json: $McpJsonPath" }
  $backup="$McpJsonPath.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
  Copy-Item -LiteralPath $McpJsonPath -Destination $backup -ErrorAction Stop
  $config=Get-Content -Raw -LiteralPath $McpJsonPath | ConvertFrom-Json
  if (!$config.mcpServers) {
    $config | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue ([pscustomobject]@{}) -Force
  }
  $config.mcpServers | Add-Member -NotePropertyName "gemco-joystick" -NotePropertyValue ([pscustomobject]$entry) -Force
  $config | ConvertTo-Json -Depth 50 | Set-Content -Encoding UTF8 -LiteralPath $McpJsonPath
  Write-Host "Configuración MCP actualizada. Respaldo: $backup"
} else {
  Write-Host "No modifiqué tu MCP original (no se proporcionó -McpJsonPath)."
  Write-Host "Usa mcp.json del repositorio o indica la ruta real al ejecutar el instalador."
}
Write-Host "INSTALADO. Ejecuta: & '$Python' '$(Join-Path $Destination 'server.py')' --self-test"
Write-Host "Luego inicia el panel: & '$Python' '$(Join-Path $Destination 'panel.py')'"
