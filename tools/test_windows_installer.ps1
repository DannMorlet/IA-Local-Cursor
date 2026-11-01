#requires -Version 5.1
[CmdletBinding()]
param([string]$OutputDir='out\setup')
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$setup=(Resolve-Path (Join-Path $root "$OutputDir\MatickStudioLM-v1.0.1-x64-Setup.exe")).Path
$sandbox=Join-Path $env:RUNNER_TEMP 'MatickInstallerSandbox'
$external=Join-Path $env:RUNNER_TEMP 'Matick-No-Tocar'
New-Item -ItemType Directory $external -Force | Out-Null
'Preservar proyecto externo' | Set-Content (Join-Path $external 'preservar.txt')
if(Test-Path $sandbox){throw 'La instalación de prueba ya existe; no sobrescribir.'}
$process=Start-Process -FilePath $setup -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',("/DIR="+$sandbox)) -Wait -PassThru
if($process.ExitCode -ne 0){throw "Error de instalación: $($process.ExitCode)"}
$exe=Join-Path $sandbox 'MatickStudioLM.exe'
$py=Join-Path $sandbox 'runtime\python.exe'
if(-not (Test-Path $exe)){throw 'EXE no instalado.'}
if(-not (Test-Path $py)){throw 'Runtime Python no instalado.'}
& $py -c 'import sqlite3, matick_cloud; print(matick_cloud.__version__)'
if($LASTEXITCODE -ne 0){throw 'Python embebido no pudo importar Matick Core.'}
$env:MATICK_RENDERER='gdi'
Remove-Item Env:MATICK_CLOUD_URL,Env:MATICK_TOKEN,Env:MATICK_TOKENS_JSON -ErrorAction SilentlyContinue
$gui=Start-Process -FilePath $exe -PassThru
$healthy=$false
try {
  for($i=0;$i -lt 30;$i++){
    $gui.Refresh()
    if($gui.HasExited){throw 'La interfaz de Matick terminó durante el arranque.'}
    try {
      $response=Invoke-RestMethod -Uri 'http://127.0.0.1:8787/health' -TimeoutSec 2
      if($response){$healthy=$true;break}
    } catch {
      Start-Sleep -Milliseconds 600
    }
  }
  if(-not $healthy){throw 'El backend local empaquetado no respondió en 8787.'}
  Write-Host 'GUI y backend local responden tras instalar.'
} finally {
  $gui.Refresh()
  if(-not $gui.HasExited){
    $gui.CloseMainWindow() | Out-Null
    if(-not $gui.WaitForExit(7000)){Stop-Process -Id $gui.Id -Force}
  }
}
$userData=Join-Path $env:LOCALAPPDATA 'MatickStudioLM\data'
New-Item -ItemType Directory $userData -Force | Out-Null
'Preservar datos de usuario' | Set-Content (Join-Path $userData 'preservar.txt')
$uninstall=Join-Path $sandbox 'unins000.exe'
if(-not (Test-Path $uninstall)){throw 'No se registró el desinstalador.'}
$result=Start-Process -FilePath $uninstall -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait -PassThru
if($result.ExitCode -ne 0){throw "Error de desinstalación: $($result.ExitCode)"}
if(Test-Path $exe){throw 'El desinstalador dejó el programa instalado.'}
if(-not (Test-Path (Join-Path $userData 'preservar.txt'))){throw 'Se borraron datos personales.'}
if(-not (Test-Path (Join-Path $external 'preservar.txt'))){throw 'Se borró un proyecto externo.'}
Write-Host 'Instalador y desinstalación segura: APROBADOS.'
