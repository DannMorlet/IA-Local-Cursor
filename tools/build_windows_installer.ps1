#requires -Version 5.1
[CmdletBinding()]
param([string]$DistDir='out\dist', [string]$OutputDir='out\setup')
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$dist=[IO.Path]::GetFullPath((Join-Path $root $DistDir))
$output=[IO.Path]::GetFullPath((Join-Path $root $OutputDir))
if(-not (Test-Path (Join-Path $dist 'runtime\python.exe'))) {
  throw 'Falta Python embebido. Ejecutar primero prepare_embedded_runtime.ps1.'
}
$compiler=Join-Path ([Environment]::GetFolderPath('ProgramFilesX86')) 'Inno Setup 6\ISCC.exe'
if(-not (Test-Path $compiler)) {
  $compiler=Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe'
}
if(-not (Test-Path $compiler)) {
  Write-Host 'Instalando Inno Setup únicamente en el runner de GitHub Actions.'
  choco install innosetup --yes --no-progress --limit-output
  if($LASTEXITCODE -ne 0){throw 'No se instaló el compilador Inno Setup.'}
  $compiler=Join-Path ([Environment]::GetFolderPath('ProgramFilesX86')) 'Inno Setup 6\ISCC.exe'
}
if(-not (Test-Path $compiler)){throw 'ISCC.exe no encontrado.'}
New-Item -ItemType Directory -Path $output -Force | Out-Null
$env:MATICK_PACKAGE_DIR=$dist
try {
  & $compiler ("/O"+$output) (Join-Path $root 'installer\MatickStudioLM.iss')
  if($LASTEXITCODE -ne 0){throw 'Error de compilación Inno Setup.'}
} finally {
  Remove-Item Env:MATICK_PACKAGE_DIR -ErrorAction SilentlyContinue
}
$setup=Join-Path $output 'MatickStudioLM-v1.0.1-x64-Setup.exe'
if(-not (Test-Path $setup)){throw 'Inno no produjo el archivo esperado.'}
Copy-Item -LiteralPath (Join-Path $root 'docs\INSTALADOR_WINDOWS_X64.md') -Destination (Join-Path $output 'LEEME_INSTALADOR.md')
$hash=(Get-FileHash -LiteralPath $setup -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  MatickStudioLM-v1.0.1-x64-Setup.exe" | Set-Content -LiteralPath (Join-Path $output 'SHA256SUMS.txt') -Encoding ASCII
Write-Host "Instalador compilado, SHA256=$hash"
