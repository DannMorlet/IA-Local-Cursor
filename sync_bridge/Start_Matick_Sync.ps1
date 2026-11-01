# Inicia Matick Sync Bridge local y prepara credencial para este PowerShell.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot
if (-not $env:MATICK_SYNC_TOKEN -or $env:MATICK_SYNC_TOKEN.Length -lt 20) {
    $bytes = [byte[]]::new(32)
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $rng.Dispose()
    $env:MATICK_SYNC_TOKEN = [Convert]::ToBase64String($bytes)
}
if (-not $env:MATICK_SYNC_PORT) { $env:MATICK_SYNC_PORT = '8788' }
$command = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } elseif (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { throw 'Instala Python 3.11 o superior.' }
$args = if ($command -eq 'py') { @('-3','-m','matick_sync.server') } else { @('-m','matick_sync.server') }
$connection = Test-NetConnection -ComputerName 127.0.0.1 -Port ([int]$env:MATICK_SYNC_PORT) -WarningAction SilentlyContinue
if ($connection.TcpTestSucceeded) { throw 'Puerto ocupado. Cierra el servidor previo antes de iniciarlo de nuevo.' }
$process = Start-Process -FilePath $command -ArgumentList $args -PassThru
Start-Sleep -Seconds 1
if ($process.HasExited) { throw 'El servicio se cerro. Revisa Python y el puerto local.' }
Write-Host 'Matick Sync Bridge iniciado localmente.' -ForegroundColor Green
Write-Host "PID: $($process.Id)  Puerto: $env:MATICK_SYNC_PORT"
Write-Host 'Las API de pago estan DESACTIVADAS de forma predeterminada.'
Write-Host 'Este PowerShell conserva MATICK_SYNC_TOKEN para usar el CLI. No compartas esa variable.'
Write-Host 'Para enviar: py -3 -m matick_sync.cli send all "Hola a los agentes"'
Write-Host 'Para escuchar: py -3 -m matick_sync.cli watch'
Write-Host 'Para finalizar: Stop-Process -Id ' $process.Id
