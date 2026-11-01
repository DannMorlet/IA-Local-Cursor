#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$CloudUrl = 'http://127.0.0.1:8787',
    [switch]$SafeMode
)
$ErrorActionPreference = 'Stop'
$exe = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path 'MatickStudioLM.exe'
if (-not (Test-Path $exe -PathType Leaf)) { throw 'Ejecutable no encontrado' }
if ($CloudUrl -notmatch '^https://[^\s]+$' -and
    $CloudUrl -notmatch '^http://(127\.0\.0\.1|localhost)(:\d+)?/?$') {
    throw 'Solo se permite HTTP en localhost o HTTPS remoto.'
}
$env:MATICK_CLOUD_URL = $CloudUrl
if (-not $env:MATICK_TOKEN) {
    Write-Warning 'Falta MATICK_TOKEN en esta sesión. La interfaz abrirá, pero no podrá enviar mensajes.'
}
Write-Host 'Abriendo Matick Studio LM desde su carpeta portable, sin tocar el proyecto de desarrollo.'
$previous = $env:MATICK_RENDERER
try {
    if ($SafeMode) {
        $env:MATICK_RENDERER = 'gdi'
        Write-Host 'Modo seguro GDI activado (sin inicializar DirectX 12).'
    }
    & $exe
} finally {
    $env:MATICK_RENDERER = $previous
    Write-Host ('Diagnostico visual: ' + (Join-Path $env:LOCALAPPDATA 'MatickStudioLM\logs\render.log'))
}
