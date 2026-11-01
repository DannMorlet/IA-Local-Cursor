#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ExePath,
    [Parameter(Mandatory = $true)][string]$OutputDir
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$exe = (Resolve-Path $ExePath).Path
if (-not (Test-Path $exe -PathType Leaf)) { throw "EXE no encontrado" }
$target = [System.IO.Path]::GetFullPath($OutputDir)
if (Test-Path $target) { throw "La carpeta de distribución ya existe: $target" }
New-Item -ItemType Directory -Path $target | Out-Null
function Copy-LightFile([string]$relative) {
    $from = Join-Path $root $relative
    if (-not (Test-Path $from -PathType Leaf)) { throw "Falta archivo obligatorio: $relative" }
    $to = Join-Path $target $relative
    $parent = Split-Path $to -Parent
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Copy-Item -LiteralPath $from -Destination $to
}
Copy-Item -LiteralPath $exe -Destination (Join-Path $target 'MatickStudioLM.exe')
foreach ($relative in @(
    'cloud/matick_cloud/__init__.py',
    'cloud/matick_cloud/__main__.py',
    'cloud/matick_cloud/server.py',
    'cloud/matick_cloud/provider.py',
    'cloud/matick_cloud/models.py',
    'cloud/matick_cloud/tasks.py',
    'cloud/matick_cloud/web/index.html',
    'cloud/matick_cloud/web/style.css',
    'cloud/matick_cloud/web/app.js',
    'cloud/matick_cloud/client.py',
    'cloud/.env.example',
    'integrations/toolhub/package.json',
    'integrations/toolhub/mcp.example.json',
    'integrations/toolhub/src/cli.mjs',
    'integrations/toolhub/src/matick-api.mjs',
    'integrations/matick-mcp/matick_mcp.py',
    'integrations/matick-mcp/mcp.example.json',
    'docs/MATICK_INDEPENDENCIA_Y_MCP.md',
    'integrations/toolhub/src/mcp-stdio.mjs',
    'integrations/toolhub/src/registry.mjs',
    'docs/PLAN_CLOUD_A_PC.md',
    'docs/REST_V1_MODELOS.md',
    'docs/DIAGNOSTICO_RENDER_WINDOWS.md',
    'tools/prepare_local_transfer.ps1',
    'tools/start_matick_portable.ps1',
    'tools/auditar_matick_pc.py',
    'tools/Auditar_Matick_PC.cmd',
    'docs/AUDITORIA_PC_1_A_100.md',
    'docs/INSTALADOR_WINDOWS_X64.md',
    'LICENSE'
)) {
    Copy-LightFile $relative
}
$forbidden = @('cuda','models','modelos','node_modules','.venv','weights','checkpoints','build','bin','obj')
$bad = Get-ChildItem -LiteralPath $target -Directory -Recurse |
    Where-Object { $forbidden -contains $_.Name.ToLowerInvariant() }
if ($bad) { throw "Distribución contiene carpetas prohibidas" }
$items = Get-ChildItem -LiteralPath $target -File -Recurse
$manifest = [ordered]@{
    name = 'Matick Studio LM'
    package_version = '1.0.1'
    independent_from_local_project = $true
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    files = @($items | ForEach-Object {
        [ordered]@{
            path = $_.FullName.Substring($target.Length + 1).Replace('\','/')
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    })
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $target 'manifest.json') -Encoding UTF8
Write-Host ("Distribución preparada con {0} archivos pequeños; sin CUDA, modelos, ni node_modules." -f $items.Count)
