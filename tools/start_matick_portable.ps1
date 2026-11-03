#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$CloudUrl,
    [switch]$SafeMode
)
$ErrorActionPreference = 'Stop'
# Accept both the source-tree layout and a portable ZIP with the script next to the EXE.
$exe = Join-Path $PSScriptRoot 'MatickStudioLM.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    $exe = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path 'MatickStudioLM.exe'
}
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw 'MatickStudioLM.exe no encontrado junto al script ni en su carpeta superior.'
}
$exe = (Resolve-Path -LiteralPath $exe).Path
$exeDir = Split-Path -Parent $exe
$explicitCloudUrl = $PSBoundParameters.ContainsKey('CloudUrl')
if ($explicitCloudUrl -and $CloudUrl -notmatch '^https://[^\s]+$' -and
    $CloudUrl -notmatch '^http://(127\.0\.0\.1|localhost)(:\d+)?/?$') {
    throw 'Solo se permite HTTP en localhost o HTTPS remoto.'
}
$previousCloudUrl = $env:MATICK_CLOUD_URL
if ($explicitCloudUrl) { $env:MATICK_CLOUD_URL = $CloudUrl }
if ($env:MATICK_CLOUD_URL -and -not $env:MATICK_TOKEN) {
    Write-Warning 'Falta MATICK_TOKEN en esta sesión. La interfaz abrirá, pero no podrá enviar mensajes.'
}
Write-Host 'Abriendo Matick Studio LM desde su carpeta portable, sin tocar el proyecto de desarrollo.'
$previous = $env:MATICK_RENDERER
try {
    if ($SafeMode) {
        $env:MATICK_RENDERER = 'gdi'
        Write-Host 'Modo seguro GDI activado (sin inicializar DirectX 12).'
    }
    # Native launchers often resolve web assets relative to the current directory.
    # Do not depend on the caller's working directory (which may contain spaces).
    Push-Location -LiteralPath $exeDir
    try {
        & $exe
    } finally {
        Pop-Location
    }
} finally {
    $env:MATICK_RENDERER = $previous
    $env:MATICK_CLOUD_URL = $previousCloudUrl
    Write-Host ('Diagnostico visual: ' + (Join-Path $env:LOCALAPPDATA 'MatickStudioLM\logs\render.log'))
}
