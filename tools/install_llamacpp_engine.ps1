#requires -Version 5.1
<#
Instala llama.cpp OFICIAL de GitHub en la carpeta de datos del usuario,
sin LM Studio, sin controladores y sin tocar C:\IA\Matick Studio LM.
La instalación es explícita, con GGUF existente y SHA256 fijo de GitHub.
Ejemplo:
  .\tools\install_llamacpp_engine.ps1 -ModelPath 'D:\Modelos\mi-modelo.Q4_K_M.gguf'
  .\tools\install_llamacpp_engine.ps1 -Backend Vulkan -ModelPath 'D:\Modelos\modelo.gguf'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateNotNullOrEmpty()][string]$ModelPath,
    [ValidateSet('Cuda13','Vulkan','Cpu')][string]$Backend = 'Cuda13',
    [ValidateRange(0,999)][int]$GpuLayers = 99,
    [ValidateRange(512,32768)][int]$ContextSize = 4096
)
$ErrorActionPreference = 'Stop'
if (-not [Environment]::Is64BitOperatingSystem) { throw 'Se requiere Windows x64.' }
if (-not $env:LOCALAPPDATA) { throw 'No hay LOCALAPPDATA.' }
$model = (Resolve-Path -LiteralPath $ModelPath -ErrorAction Stop).Path
if ([IO.Path]::GetExtension($model) -ine '.gguf') { throw 'Selecciona un modelo .gguf real.' }
$stream = [IO.File]::OpenRead($model)
try {
    $head = New-Object byte[] 4
    if ($stream.Read($head, 0, 4) -ne 4 -or [Text.Encoding]::ASCII.GetString($head) -ne 'GGUF') {
        throw 'El archivo no tiene la cabecera GGUF.'
    }
} finally { $stream.Dispose() }
if ($Backend -eq 'Cpu') { $GpuLayers = 0 }
$tag = 'b12099'  # versión revisada el 4 nov 2026, no descargar latest sin verificaciones
$base = "https://github.com/ggml-org/llama.cpp/releases/download/$tag"
$packages = switch ($Backend) {
    'Cuda13' {
        @(
            @{Name="llama-b12099-bin-win-cuda-13.4-x64.zip"; SHA256="4217dcfaceed745237695e9d09bed5c6189d34d3d3873fb3686bb50ad8599670"},
            @{Name="cudart-llama-bin-win-cuda-13.4-x64.zip"; SHA256="738f8c251ac22b70c3ae6f83a10cf222725df0395246a2cf58f32bdb85fbe668"}
        )
    }
    'Vulkan' {
        @(@{Name="llama-b12099-bin-win-vulkan-x64.zip"; SHA256="a3c901e3289eff7bfbe1315e855bba3026ef03929c88f6104a1d9bf8b093450b"})
    }
    'Cpu' {
        @(@{Name="llama-b12099-bin-win-cpu-x64.zip"; SHA256="ba751a91caeb8f5492c408386a46c9e0eba7da599c81bce1383260342e2b672b"})
    }
}
$home = Join-Path $env:LOCALAPPDATA 'MatickStudioLM'
$engines = Join-Path $home 'engines'
$version = "$tag-$($Backend.ToLowerInvariant())"
$destination = Join-Path $engines $version
$config = Join-Path $home 'inference.json'
$work = Join-Path $env:TEMP ("matick-llamacpp-" + [guid]::NewGuid().ToString('N'))
$stage = Join-Path $engines ("$version-stage-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $engines, $work, $stage | Out-Null
try {
    if (Test-Path -LiteralPath $destination) {
        if (-not (Test-Path -LiteralPath (Join-Path $destination 'llama-server.exe'))) {
            throw "La carpeta de versión ya existe pero está incompleta: $destination"
        }
        Write-Host "Motor ya descargado: $destination"
    } else {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $counter = 0
        foreach ($package in $packages) {
            $counter++
            $archive = Join-Path $work $package.Name
            Write-Host "Descargando $($package.Name) desde el repositorio oficial..."
            Invoke-WebRequest -Uri "$base/$($package.Name)" -OutFile $archive -UseBasicParsing
            $actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($actual -ne $package.SHA256) {
                throw "SHA256 no coincide para $($package.Name). No se instalará."
            }
            $part = Join-Path $work "part$counter"
            Expand-Archive -LiteralPath $archive -DestinationPath $part -Force
            if ($counter -eq 1) {
                $server = Get-ChildItem -LiteralPath $part -Filter 'llama-server.exe' -Recurse -File | Select-Object -First 1
                if (-not $server) { throw 'El archivo oficial no contiene llama-server.exe.' }
                # -LiteralPath no admite comodines: copiar el contenido mediante Get-ChildItem.
                Get-ChildItem -LiteralPath $server.DirectoryName -Force | ForEach-Object {
                    Copy-Item -LiteralPath $_.FullName -Destination $stage -Recurse -Force
                }
            } else {
                # El segundo ZIP oficial aporta bibliotecas CUDA en tiempo de ejecución.
                Get-ChildItem -LiteralPath $part -File -Recurse -Filter '*.dll' | ForEach-Object {
                    $targetDll = Join-Path $stage $_.Name
                    if (-not (Test-Path -LiteralPath $targetDll)) {
                        Copy-Item -LiteralPath $_.FullName -Destination $targetDll
                    }
                }
            }
        }
        if (-not (Test-Path -LiteralPath (Join-Path $stage 'llama-server.exe'))) {
            throw 'No se encontró llama-server.exe tras extraer los paquetes.'
        }
        Move-Item -LiteralPath $stage -Destination $destination
    }
    $entry = [ordered]@{
        enabled = $true
        backend = 'llama.cpp'
        executable = (Join-Path $destination 'llama-server.exe')
        model_path = $model
        gpu_layers = $GpuLayers
        context_size = $ContextSize
    }
    if (Test-Path -LiteralPath $config) {
        $backup = "$config.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item -LiteralPath $config -Destination $backup
        Write-Host "Respaldo de configuración: $backup"
    }
    $tempConfig = "$config.tmp"
    $entry | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $tempConfig -Encoding UTF8
    Move-Item -LiteralPath $tempConfig -Destination $config -Force
    Write-Host 'Motor local configurado para Matick Studio LM.' -ForegroundColor Green
    Write-Host "Backend: $Backend | GGUF: $model | Puerto: 127.0.0.1:18776"
    Write-Host 'Abre la NUEVA compilación de Matick Studio LM y espera la carga del modelo.'
    Write-Host 'No se modificaron drivers, LM Studio, ni C:\IA\Matick Studio LM.'
} finally {
    if (Test-Path -LiteralPath $work) { Remove-Item -LiteralPath $work -Recurse -Force }
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
}
