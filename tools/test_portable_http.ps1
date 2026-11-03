#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$DistPath)
$ErrorActionPreference = 'Stop'
$dist = (Resolve-Path -LiteralPath $DistPath).Path
$exe = Join-Path $dist 'MatickStudioLM.exe'
if (Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue) {
    throw 'Puerto 8787 ocupado: no se probará contra un servicio ajeno.'
}
$saved = @{}
$names = @('LOCALAPPDATA','MATICK_RENDERER','MATICK_CLOUD_URL','MATICK_TOKEN','MATICK_TOKENS_JSON')
foreach ($name in $names) { $saved[$name] = [Environment]::GetEnvironmentVariable($name,'Process') }
$sandbox = Join-Path ([IO.Path]::GetTempPath()) ('Matick HTTP con espacios ' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $sandbox | Out-Null
try {
    $env:LOCALAPPDATA = $sandbox
    $env:MATICK_RENDERER = 'gdi'
    Remove-Item Env:MATICK_CLOUD_URL,Env:MATICK_TOKEN,Env:MATICK_TOKENS_JSON -ErrorAction SilentlyContinue
    $gui = Start-Process -FilePath $exe -WorkingDirectory $sandbox -PassThru
    $ready = $false
    for ($i=0; $i -lt 40; $i++) {
        $gui.Refresh()
        if ($gui.HasExited) { throw 'El launcher terminó durante el arranque.' }
        try {
            $health = Invoke-RestMethod 'http://127.0.0.1:8787/health' -TimeoutSec 2
            if ($health.service -eq 'matick-studio-lm-cloud' -and $health.version -eq '1.2.0') { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 250 }
    }
    if (-not $ready) { throw 'No respondió el backend Matick 1.2.0.' }
    foreach ($asset in @('app.js','chat_payload.mjs','clare.js','clare_behavior.mjs','clare.css','style.css')) {
        $response = Invoke-WebRequest ("http://127.0.0.1:8787/app/"+$asset) -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -ne 200 -or $response.RawContentLength -eq 0) { throw "Recurso inválido: $asset" }
    }
    $trace = Get-Content -LiteralPath (Join-Path $sandbox 'MatickStudioLM/logs/render.log') -Raw
    foreach ($mark in @('WINDOW_VISIBLE','GDI_SAFE_MODE_USER_SELECTED','BACKEND_STARTED_ISOLATED')) {
        if (-not $trace.Contains($mark)) { throw "Falta evidencia: $mark" }
    }
    Write-Host 'APROBADO: launcher x64, backend 1.2.0, HTTP y recursos desde ruta con espacios; GDI solicitado.'
} finally {
    if ($gui) {
        $gui.Refresh()
        if (-not $gui.HasExited) {
            $gui.CloseMainWindow() | Out-Null
            if (-not $gui.WaitForExit(15000)) { Stop-Process -Id $gui.Id -Force }
        }
    }
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$saved[$name],'Process') }
    Write-Host "Evidencia temporal conservada en $sandbox"
}
# El cierre del Job termina al hijo de forma asíncrona; esperar un límite finito.
for ($i=0; $i -lt 50; $i++) {
    if (-not (Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue)) { break }
    Start-Sleep -Milliseconds 100
}
if (Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue) {
    throw 'El backend no se cerró junto con el launcher.'
}
