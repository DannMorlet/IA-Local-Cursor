#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) ('Matick missing EXE ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root -Force | Out-Null
try {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\start_matick_portable.ps1') -Destination (Join-Path $root 'start_matick_portable.ps1')
    $failure = $null
    try {
        & (Join-Path $root 'start_matick_portable.ps1') -SafeMode
    } catch {
        $failure = $_.Exception.Message
    }
    if ($failure -notmatch 'MatickStudioLM\.exe no encontrado') {
        throw ('El launcher no explicó que falta el EXE: ' + $failure)
    }
    Write-Host 'APROBADO: EXE ausente produce diagnóstico legible.'
} finally {
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
$global:LASTEXITCODE = 0
