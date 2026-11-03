#requires -Version 5.1
[CmdletBinding()]
param(
  [string]$OutputDir = 'out\llama-runtime',
  [string]$SourceDir = 'out\third-party\llama.cpp',
  [string]$BuildDir = 'out\llama-build'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$source = [IO.Path]::GetFullPath((Join-Path $root $SourceDir))
$build = [IO.Path]::GetFullPath((Join-Path $root $BuildDir))
$target = [IO.Path]::GetFullPath((Join-Path $root $OutputDir))
if (Test-Path -LiteralPath $source) { throw 'Ya existe la carpeta fuente: no sobreescribir' }
if (Test-Path -LiteralPath $target) { throw 'Ya existe la carpeta destino: no sobreescribir' }
New-Item -ItemType Directory -Force -Path (Split-Path $source -Parent) | Out-Null
# Tag verificado el 03/11/2026; fuente MIT. Pinned SHA prevents repointing tag.
$tag = 'v0.8.0'
$sha = '8642541b255bfb5dc39cd351a178be09013a55d6'
& git clone --depth 1 --branch $tag --single-branch https://github.com/ggml-org/llama.cpp.git $source
if ($LASTEXITCODE -ne 0) { throw 'No se pudo obtener llama.cpp oficial' }
$actual = (& git -C $source rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actual -ne $sha) { throw "llama.cpp inesperado: $actual" }
& cmake -S $source -B $build -G 'Visual Studio 17 2022' -A x64 -DLLAMA_BUILD_SERVER=ON -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DGGML_CUDA=OFF -DGGML_NATIVE=OFF
if ($LASTEXITCODE -ne 0) { throw 'Configuracion CMake llama.cpp fallida' }
& cmake --build $build --config Release --target llama-server --parallel 4
if ($LASTEXITCODE -ne 0) { throw 'Compilacion llama-server CPU fallida' }
$exe = Get-ChildItem -LiteralPath $build -File -Filter 'llama-server.exe' -Recurse |
  Where-Object { $_.FullName -match '[\\/]Release[\\/]' } | Select-Object -First 1
if (-not $exe) { throw 'No se genero llama-server.exe' }
New-Item -ItemType Directory -Force -Path $target | Out-Null
Copy-Item -LiteralPath $exe.FullName -Destination (Join-Path $target 'llama-server.exe')
$libDir = Split-Path $exe.FullName -Parent
Get-ChildItem -LiteralPath $libDir -Filter '*.dll' -File |
  ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $target }
Copy-Item -LiteralPath (Join-Path $source 'LICENSE') -Destination (Join-Path $target 'LICENSE-llama.cpp.txt')
@"
llama.cpp $tag (CPU x64; sin CUDA)
Upstream: https://github.com/ggml-org/llama.cpp
Commit: $sha
Este binario es un respaldo CPU. Para NVIDIA RTX se requiere un build CUDA compatible independiente.
No incluye modelos ni NVIDIA drivers.
"@ | Set-Content -LiteralPath (Join-Path $target 'BUILD-INFO.txt') -Encoding UTF8
& (Join-Path $target 'llama-server.exe') --version
if ($LASTEXITCODE -ne 0) { throw 'El ejecutable no supera --version' }
Write-Host ('llama.cpp CPU listo: ' + (Get-ChildItem -LiteralPath $target -File | Measure-Object -Property Length -Sum).Sum + ' bytes')
