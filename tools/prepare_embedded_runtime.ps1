#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$DistPath)
$ErrorActionPreference = 'Stop'
$dist = [IO.Path]::GetFullPath($DistPath)
$pythonVersion = '3.12.10'
$url = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-embed-amd64.zip"
$expectedSha256 = '4ACBED6DD1C744B0376E3B1CF57CE906F9DC9E95E68824584C8099A63025A3C3'
$runtime = Join-Path $dist 'runtime'
if (-not (Test-Path (Join-Path $dist 'MatickStudioLM.exe'))) { throw 'Falta el programa x64.' }
if (-not (Test-Path (Join-Path $dist 'cloud/matick_cloud/server.py'))) { throw 'Falta Matick Core.' }
if (Test-Path $runtime) { throw 'No sobrescribir runtime existente.' }
New-Item -ItemType Directory $runtime -Force | Out-Null
$archive = Join-Path $env:RUNNER_TEMP "python-$pythonVersion-embed-amd64.zip"
if (-not $env:RUNNER_TEMP) { $archive = Join-Path $env:TEMP "python-$pythonVersion-embed-amd64.zip" }
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $archive -UseBasicParsing
    $found = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash
    if ($found -ine $expectedSha256) {
        throw "SHA256 de Python no coincide, no se instalará ($found)."
    }
    Expand-Archive -LiteralPath $archive -DestinationPath $runtime -Force
} finally {
    if (Test-Path $archive) { Remove-Item $archive -Force }
}
$pth = Join-Path $runtime 'python312._pth'
if (-not (Test-Path -LiteralPath $pth)) { throw 'El runtime oficial no contiene python312._pth.' }
# Restringe Python al stdlib + paquete Matick. No importa site-packages ni Python global.
@('python312.zip', '.', '..\cloud') | Set-Content -LiteralPath $pth -Encoding ASCII
$py = Join-Path $runtime 'python.exe'
& $py -c "import sys, sqlite3, matick_cloud; assert sys.version_info[:2] == (3,12); print('Matick Core + SQLite + Python aislado listos')"
if ($LASTEXITCODE -ne 0) { throw 'No funciona el backend Python embebido.' }
# Documentar permisos y los componentes empaquetados mediante un manifiesto completo.
$items = Get-ChildItem -LiteralPath $dist -File -Recurse | Where-Object { $_.Name -ne 'manifest.json' }
$manifest = [ordered]@{
    name = 'Matick Studio LM Cloud'
    package_version = '1.0.1'
    architecture = 'windows-x64'
    python_runtime = "$pythonVersion (PSF License, archivos runtime/LICENSE.txt)"
    runtime_source = $url
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    files = @($items | ForEach-Object {
        [ordered]@{
            path = $_.FullName.Substring($dist.Length + 1).Replace('\','/')
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    })
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $dist 'manifest.json') -Encoding UTF8
Write-Host ("Matick empaquetado: {0} archivos, Python {1}, sin modelos/CUDA." -f $items.Count, $pythonVersion)
