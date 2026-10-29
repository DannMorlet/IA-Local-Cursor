# Agente de código local usando Aider + LM Studio. No incluye claves de nube.
# Instalar Aider por separado, siguiendo https://aider.chat/docs/install.html
param(
    [Parameter(Mandatory = $true)]
    [string]$ModelId,
    [string]$Project = "."
)
$ErrorActionPreference = "Stop"
if (-not (Get-Command aider -ErrorAction SilentlyContinue)) {
    throw "Aider no está instalado. Consulta https://aider.chat/docs/install.html"
}
if (-not (Test-Path -LiteralPath $Project -PathType Container)) {
    throw "Carpeta del proyecto no encontrada"
}
$env:LM_STUDIO_API_KEY = "lm-studio-local-no-real-key"
$env:LM_STUDIO_API_BASE = "http://127.0.0.1:1234/v1"
Push-Location (Resolve-Path -LiteralPath $Project).Path
try {
    Write-Host "Modelo: $ModelId | Directorio: $(Get-Location)"
    Write-Host "Revisa las acciones y los diffs antes de aceptar cambios."
    aider --model "lm_studio/$ModelId"
} finally {
    Pop-Location
}
