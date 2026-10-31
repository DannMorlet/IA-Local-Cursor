#requires -Version 5.1
<# 
 Comparación y preparación de traslado, opt-in y sin modificar el proyecto local.
 Modo normal: únicamente muestra planes. -Stage prepara una carpeta NUEVA,
 nunca reemplaza archivos de C:\IA\Matick Studio LM.
#>
[CmdletBinding()]
param(
    [string]$LocalRoot = 'C:\IA\Matick Studio LM',
    [switch]$Stage,
    [string]$StageName = '_Matick_GitHub_Revision'
)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$exe = Join-Path $source 'MatickStudioLM.exe'
$manifestPath = Join-Path $source 'manifest.json'
if (-not (Test-Path $exe -PathType Leaf)) { throw 'Falta MatickStudioLM.exe en el paquete portable' }
if (-not (Test-Path $manifestPath -PathType Leaf)) { throw 'Falta manifest.json. Descarga el paquete completo de GitHub Actions' }
if (-not (Test-Path $LocalRoot -PathType Container)) {
    Write-Host "El proyecto local todavía no se encuentra en $LocalRoot; no se creará ni modificará."
}
$destination = Join-Path $LocalRoot $StageName
if (-not $Stage) {
    Write-Host 'SIMULACIÓN: no se ha copiado nada.'
    Write-Host "Paquete fuente: $source"
    Write-Host "Proyecto local, protegido: $LocalRoot"
    Write-Host "Carpeta NUEVA propuesta: $destination"
    Write-Host "Usa -Stage exclusivamente si quieres crear esa carpeta aparte."
    exit 0
}
if (-not (Test-Path $LocalRoot -PathType Container)) {
    throw 'La carpeta del proyecto local no existe. Se cancela para evitar instalar en otro sitio.'
}
if (-not ($StageName -match '^_[a-zA-Z0-9_-]{5,70}$')) {
    throw 'StageName debe iniciar con _ y usar solo letras, dígitos, guiones y _.'
}
if (Test-Path $destination) { throw 'La carpeta de revisión ya existe: no se sobrescribe.' }
$files = @((Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json).files)
if (-not $files -or $files.Count -lt 5) { throw 'Manifiesto inválido o incompleto' }
foreach ($item in $files) {
    $relative = [string]$item.path
    if ($relative.Contains('..') -or $relative.StartsWith('/') -or $relative.Contains(':')) {
        throw 'Archivo inseguro en el manifiesto'
    }
    $path = Join-Path $source $relative
    if (-not (Test-Path $path -PathType Leaf)) { throw "Falta el archivo $relative" }
    $digest = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    if ($digest -ine [string]$item.sha256) { throw "Hash SHA256 no coincide: $relative" }
}
# Solo se crea un directorio hermano lógico dentro del proyecto; no se mezclan DLLs ni scripts.
New-Item -ItemType Directory -Path $destination | Out-Null
foreach ($item in $files) {
    $relative = [string]$item.path
    $from = Join-Path $source $relative
    $to = Join-Path $destination $relative
    New-Item -ItemType Directory -Path (Split-Path $to -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $from -Destination $to -ErrorAction Stop
}
Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $destination 'manifest.json')
Write-Host "Preparado en carpeta nueva: $destination"
Write-Host 'Tu programa actual no se reemplazó. Revisa ambas versiones antes de integrar.'
