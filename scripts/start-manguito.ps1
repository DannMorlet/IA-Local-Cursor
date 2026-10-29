param(
    [string]$Workspace = (Join-Path $HOME "ManguitoWorkspace"),
    [switch]$AllowWrites
)
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Workspace)) {
    New-Item -ItemType Directory -Force -Path $Workspace | Out-Null
}
$env:MANGUITO_WORKSPACE = (Resolve-Path -LiteralPath $Workspace).Path

if (-not $env:MANGUITO_MODEL_URL) {
    $env:MANGUITO_MODEL_URL = "http://127.0.0.1:1234/v1"
}
if (-not $env:MANGUITO_TOKEN) {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $env:MANGUITO_TOKEN = [Convert]::ToBase64String($bytes)
    Write-Host "TOKEN SOLO DE ESTA SESIÓN (NO COMPARTIR): $env:MANGUITO_TOKEN"
}
$env:MANGUITO_ENABLE_WRITES = if ($AllowWrites) { "1" } else { "0" }
Write-Host "Workspace: $env:MANGUITO_WORKSPACE"
Write-Host "Servidor LLM: $env:MANGUITO_MODEL_URL"
Write-Host "Escrituras habilitadas: $env:MANGUITO_ENABLE_WRITES"
Push-Location (Join-Path $PSScriptRoot "..")
try {
    python -m manguito.gateway
} finally {
    Pop-Location
}
