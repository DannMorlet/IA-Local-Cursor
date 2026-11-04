#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) ('Matick launcher smoke ' + [guid]::NewGuid().ToString('N'))
$previousCloudUrl = $env:MATICK_CLOUD_URL
$previousToken = $env:MATICK_TOKEN
$previousRenderer = $env:MATICK_RENDERER
$previousLocalAppData = $env:LOCALAPPDATA
$previousLocation = (Get-Location).Path
New-Item -ItemType Directory -Path $root -Force | Out-Null
try {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\start_matick_portable.ps1') -Destination (Join-Path $root 'start_matick_portable.ps1')
    $source = 'public static class MatickTestExit { public static int Main() { return 17; } }'
    Add-Type -TypeDefinition $source -OutputAssembly (Join-Path $root 'MatickStudioLM.exe') -OutputType ConsoleApplication
    $env:MATICK_CLOUD_URL = 'http://127.0.0.1:18776'
    $env:MATICK_TOKEN = 'test-only'
    $env:MATICK_RENDERER = 'dx12'
    $caughtMessage = $null
    try {
        & (Join-Path $root 'start_matick_portable.ps1') -SafeMode
    } catch {
        $caughtMessage = $_.Exception.Message
    }
    if (-not $caughtMessage) { throw 'El launcher no lanzó ninguna excepción ante el código 17.' }
    if ($caughtMessage -notmatch 'código de salida 17') {
        throw ('El launcher falló por una causa inesperada: ' + $caughtMessage)
    }
    if ((Get-Location).Path -ne $previousLocation) {
        throw 'El launcher no restauró el directorio del llamador tras fallar.'
    }
    if ($env:MATICK_RENDERER -ne 'dx12') {
        throw 'El launcher no restauró el renderizador tras fallar.'
    }
    if ($env:MATICK_CLOUD_URL -ne 'http://127.0.0.1:18776' -or $env:MATICK_TOKEN -ne 'test-only') {
        throw 'El launcher modificó la configuración heredada tras fallar.'
    }
    # A rejected inherited URL must stop before launching the native EXE.
    # The stub would exit 17 if executed; an early URL validation error is distinct.
    $env:MATICK_CLOUD_URL = 'http://example.invalid:18776'
    $blockedMessage = $null
    try {
        & (Join-Path $root 'start_matick_portable.ps1') -SafeMode
    } catch {
        $blockedMessage = $_.Exception.Message
    }
    if (-not $blockedMessage -or $blockedMessage -notmatch 'Solo se permite HTTP en localhost o HTTPS remoto') {
        throw ('La URL HTTP heredada no se rechazó antes de ejecutar el EXE: ' + $blockedMessage)
    }
    if ((Get-Location).Path -ne $previousLocation -or $env:MATICK_RENDERER -ne 'dx12') {
        throw 'El rechazo de URL alteró el directorio o renderizador del llamador.'
    }
    # An explicit safe URL must override an unsafe inherited value without
    # permanently changing the environment, even if the native process fails.
    $env:MATICK_CLOUD_URL = 'http://example.invalid:18776'
    $explicitFailure = $null
    try {
        & (Join-Path $root 'start_matick_portable.ps1') -CloudUrl 'http://127.0.0.1:18776' -SafeMode
    } catch {
        $explicitFailure = $_.Exception.Message
    }
    if ($explicitFailure -notmatch 'código de salida 17') {
        throw ('La URL explícita segura no prevaleció sobre la heredada: ' + $explicitFailure)
    }
    if ($env:MATICK_CLOUD_URL -ne 'http://example.invalid:18776' -or
        $env:MATICK_RENDERER -ne 'dx12' -or (Get-Location).Path -ne $previousLocation) {
        throw 'El launcher no restauró el entorno tras utilizar -CloudUrl explícita.'
    }
    # A missing LOCALAPPDATA must not hide the native exit code 17.
    $env:MATICK_CLOUD_URL = 'http://127.0.0.1:18776'
    $env:LOCALAPPDATA = $null
    $missingAppDataFailure = $null
    try {
        & (Join-Path $root 'start_matick_portable.ps1') -SafeMode
    } catch {
        $missingAppDataFailure = $_.Exception.Message
    }
    if ($missingAppDataFailure -notmatch 'código de salida 17') {
        throw ('LOCALAPPDATA ausente ocultó el error nativo: ' + $missingAppDataFailure)
    }
    Write-Host 'APROBADO: código de salida y restauración de entorno/directorio.'
} finally {
    $env:MATICK_CLOUD_URL = $previousCloudUrl
    $env:MATICK_TOKEN = $previousToken
    $env:MATICK_RENDERER = $previousRenderer
    $env:LOCALAPPDATA = $previousLocalAppData
    Set-Location -LiteralPath $previousLocation
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}

# PowerShell 5.1 returns the last native process exit code even when its
# expected failure was caught and all assertions passed. Reset it only after
# successful completion; thrown assertions still fail the workflow.
$global:LASTEXITCODE = 0
