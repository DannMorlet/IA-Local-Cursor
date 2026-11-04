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
    $exe = Join-Path (Join-Path $PSScriptRoot '..') 'MatickStudioLM.exe'
}
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw 'MatickStudioLM.exe no encontrado junto al script ni en su carpeta superior.'
}
$exe = (Resolve-Path -LiteralPath $exe).Path
$exeDir = Split-Path -Parent $exe
$explicitCloudUrl = $PSBoundParameters.ContainsKey('CloudUrl')
$previousCloudUrl = $env:MATICK_CLOUD_URL
# Validate inherited settings as well as explicit arguments before starting the EXE.
# An unsafe inherited HTTP URL must never silently redirect an authenticated chat.
$effectiveCloudUrl = if ($explicitCloudUrl) { $CloudUrl } else { $previousCloudUrl }
if ($effectiveCloudUrl) {
    $parsedUrl = $null
    $validAbsoluteUrl = [Uri]::TryCreate($effectiveCloudUrl, [UriKind]::Absolute, [ref]$parsedUrl)
    $loopbackHost = $validAbsoluteUrl -and $parsedUrl.Host -in @('127.0.0.1', 'localhost', '::1')
    $allowedScheme = $validAbsoluteUrl -and (
        $parsedUrl.Scheme -eq 'https' -or ($parsedUrl.Scheme -eq 'http' -and $loopbackHost)
    )
    # Do not allow embedded URL credentials: tokens belong in MATICK_TOKEN.
    if (-not $allowedScheme -or $parsedUrl.UserInfo -or $parsedUrl.Fragment) {
        throw 'Solo se permite HTTP en localhost o HTTPS remoto, sin credenciales ni fragmentos en URL.'
    }
}
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
        if ($LASTEXITCODE -ne 0) {
            throw "MatickStudioLM.exe terminó con código de salida $LASTEXITCODE. Revise el registro render.log."
        }
    } finally {
        Pop-Location
    }
} finally {
    $env:MATICK_RENDERER = $previous
    $env:MATICK_CLOUD_URL = $previousCloudUrl
    # Diagnostics must never mask the original native error when LOCALAPPDATA is absent.
    if ($env:LOCALAPPDATA) {
        Write-Host ('Diagnostico visual: ' + (Join-Path $env:LOCALAPPDATA 'MatickStudioLM\logs\render.log'))
    } else {
        Write-Warning 'LOCALAPPDATA no definido; consulte render.log junto al ejecutable si existe.'
    }
}
