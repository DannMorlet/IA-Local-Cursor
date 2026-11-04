#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) ('Matick launcher smoke ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root -Force | Out-Null
try {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\start_matick_portable.ps1') -Destination (Join-Path $root 'start_matick_portable.ps1')
    $source = 'public static class MatickTestExit { public static int Main() { return 17; } }'
    Add-Type -TypeDefinition $source -OutputAssembly (Join-Path $root 'MatickStudioLM.exe') -OutputType ConsoleApplication
    $env:MATICK_CLOUD_URL = 'http://127.0.0.1:18776'
    $env:MATICK_TOKEN = 'test-only'
    $failed = $false
    try {
        & (Join-Path $root 'start_matick_portable.ps1') -SafeMode
    } catch {
        $failed = $_.Exception.Message -match 'código de salida 17'
    }
    if (-not $failed) { throw 'El launcher ocultó el código de salida 17.' }
    Write-Host 'APROBADO: el launcher comunica fallos reales del ejecutable.'
} finally {
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
