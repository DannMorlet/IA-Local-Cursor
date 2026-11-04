#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) ('Matick launcher smoke ' + [guid]::NewGuid().ToString('N'))
$previousCloudUrl = $env:MATICK_CLOUD_URL
$previousToken = $env:MATICK_TOKEN
$previousRenderer = $env:MATICK_RENDERER
$previousLocation = (Get-Location).Path
New-Item -ItemType Directory -Path $root -Force | Out-Null
try {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\start_matick_portable.ps1') -Destination (Join-Path $root 'start_matick_portable.ps1')
    $source = 'public static class MatickTestExit { public static int Main() { return 17; } }'
    Add-Type -TypeDefinition $source -OutputAssembly (Join-Path $root 'MatickStudioLM.exe') -OutputType ConsoleApplication
    $env:MATICK_CLOUD_URL = 'http://127.0.0.1:18776'
    $env:MATICK_TOKEN = 'test-only'
    $env:MATICK_RENDERER = 'dx12'
    $failed = $false
    try {
        & (Join-Path $root 'start_matick_portable.ps1') -SafeMode
    } catch {
        $failed = $_.Exception.Message -match 'código de salida 17'
    }
    if (-not $failed) { throw 'El launcher ocultó el código de salida 17.' }
    if ((Get-Location).Path -ne $previousLocation) {
        throw 'El launcher no restauró el directorio del llamador tras fallar.'
    }
    if ($env:MATICK_RENDERER -ne 'dx12') {
        throw 'El launcher no restauró el renderizador tras fallar.'
    }
    if ($env:MATICK_CLOUD_URL -ne 'http://127.0.0.1:18776' -or $env:MATICK_TOKEN -ne 'test-only') {
        throw 'El launcher modificó la configuración heredada tras fallar.'
    }
    Write-Host 'APROBADO: código de salida y restauración de entorno/directorio.'
} finally {
    $env:MATICK_CLOUD_URL = $previousCloudUrl
    $env:MATICK_TOKEN = $previousToken
    $env:MATICK_RENDERER = $previousRenderer
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
