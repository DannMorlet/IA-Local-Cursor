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
    # URL credentials must not be accepted: the launcher uses MATICK_TOKEN.
    # The native stub would return 17 if URL validation failed to run first.
    foreach ($unsafeUrl in @('https://user:pass@example.com/v1', 'https://example.com/v1#secret', 'https:///', 'http://example.com/v1')) {
        $env:MATICK_CLOUD_URL = $unsafeUrl
        $unsafeMessage = $null
        try {
            & (Join-Path $root 'start_matick_portable.ps1') -SafeMode
        } catch {
            $unsafeMessage = $_.Exception.Message
        }
        if ($unsafeMessage -notmatch 'Solo se permite HTTP en localhost o HTTPS remoto') {
            throw ('URL insegura no rechazada antes de iniciar EXE: ' + $unsafeUrl + ' -> ' + $unsafeMessage)
        }
        if ($env:MATICK_CLOUD_URL -ne $unsafeUrl -or $env:MATICK_RENDERER -ne 'dx12' -or
            (Get-Location).Path -ne $previousLocation) {
            throw ('Rechazo de URL alteró entorno: ' + $unsafeUrl)
        }
    }
    # Port zero is not a usable HTTP endpoint. Reject before invoking the EXE.
    # A native stub exit 17 would mean the preflight failed to protect the user.
    foreach ($invalidPortUrl in @('http://127.0.0.1:0/v1', 'https://example.com:0/v1')) {
        $env:MATICK_CLOUD_URL = $invalidPortUrl
        $portFailure = $null
        try {
            & (Join-Path $root 'start_matick_portable.ps1') -SafeMode
        } catch {
            $portFailure = $_.Exception.Message
        }
        if ($portFailure -notmatch 'Solo se permite HTTP en localhost o HTTPS remoto') {
            throw ('Puerto cero no rechazado antes del EXE: ' + $invalidPortUrl + ' -> ' + $portFailure)
        }
        if ($env:MATICK_CLOUD_URL -ne $invalidPortUrl -or
            $env:MATICK_RENDERER -ne 'dx12' -or (Get-Location).Path -ne $previousLocation) {
            throw ('Puerto cero alteró el entorno del llamador: ' + $invalidPortUrl)
        }
    }
    # A loopback URL with a path is valid for a REST v1 endpoint.
    $env:MATICK_CLOUD_URL = 'http://127.0.0.1:18776/v1'
    $loopbackFailure = $null
    try {
        & (Join-Path $root 'start_matick_portable.ps1') -SafeMode
    } catch {
        $loopbackFailure = $_.Exception.Message
    }
    if ($loopbackFailure -notmatch 'código de salida 17') {
        throw ('Ruta REST local rechazada inesperadamente: ' + $loopbackFailure)
    }
    if ($env:MATICK_CLOUD_URL -ne 'http://127.0.0.1:18776/v1') {
        throw 'El launcher no restauró URL local con ruta.'
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
    # The missing-LOCALAPPDATA error path must preserve every caller setting.
    if ($env:MATICK_CLOUD_URL -ne 'http://127.0.0.1:18776' -or
        $env:MATICK_TOKEN -ne 'test-only' -or
        $env:MATICK_RENDERER -ne 'dx12' -or
        $null -ne $env:LOCALAPPDATA -or
        (Get-Location).Path -ne $previousLocation) {
        throw 'LOCALAPPDATA ausente alteró entorno o directorio tras fallar el EXE.'
    }
    # Portable source-tree layout: launcher script lives in tools/ and EXE in parent.
    # Both paths contain spaces; the EXE stub still exits 17, proving it ran.
    $nestedTools = Join-Path $root 'sub folder'
    New-Item -ItemType Directory -Path $nestedTools -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $root 'start_matick_portable.ps1') -Destination (Join-Path $nestedTools 'start_matick_portable.ps1')
    $env:LOCALAPPDATA = $previousLocalAppData
    $env:MATICK_CLOUD_URL = 'http://127.0.0.1:18776'
    $nestedFailure = $null
    try {
        & (Join-Path $nestedTools 'start_matick_portable.ps1') -SafeMode
    } catch {
        $nestedFailure = $_.Exception.Message
    }
    if ($nestedFailure -notmatch 'código de salida 17') {
        throw ('Layout EXE padre con espacios no ejecutó el binario: ' + $nestedFailure)
    }
    if ((Get-Location).Path -ne $previousLocation -or
        $env:MATICK_RENDERER -ne 'dx12' -or
        $env:MATICK_CLOUD_URL -ne 'http://127.0.0.1:18776') {
        throw 'Layout EXE padre no restauró entorno o directorio.'
    }
    # HTTPS remote endpoints remain supported after tightening URL validation.
    # A valid remote URL must reach the stub (exit 17), not fail preflight.
    $env:MATICK_CLOUD_URL = 'https://example.com/v1'
    $httpsFailure = $null
    try {
        & (Join-Path $root 'start_matick_portable.ps1') -SafeMode
    } catch {
        $httpsFailure = $_.Exception.Message
    }
    if ($httpsFailure -notmatch 'código de salida 17') {
        throw ('HTTPS remoto válido fue rechazado o no ejecutó EXE: ' + $httpsFailure)
    }
    if ($env:MATICK_CLOUD_URL -ne 'https://example.com/v1' -or
        $env:MATICK_RENDERER -ne 'dx12' -or (Get-Location).Path -ne $previousLocation) {
        throw 'HTTPS remoto válido no restauró el entorno o directorio.'
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

& (Join-Path $PSScriptRoot 'test_launcher_missing_exe.ps1')

# PowerShell 5.1 returns the last native process exit code even when its
# expected failure was caught and all assertions passed. Reset it only after
# successful completion; thrown assertions still fail the workflow.
$global:LASTEXITCODE = 0
