# Diagnóstico SIN modificación del equipo ni recopilación de archivos personales.
$ErrorActionPreference = "Continue"
Write-Host "--- Sistema operativo ---"
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber
Write-Host "--- CPU ---"
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors
Write-Host "--- RAM instalada ---"
Get-CimInstance Win32_PhysicalMemory | Select-Object Manufacturer, Capacity, Speed, ConfiguredClockSpeed
Write-Host "--- Tarjetas gráficas ---"
Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion
Write-Host "--- CUDA/NVIDIA, si existe ---"
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader
} else {
    Write-Host "No se encontró nvidia-smi en PATH"
}
Write-Host "--- Dispositivos NPU ---"
Get-PnpDevice -PresentOnly | Where-Object {
    $_.FriendlyName -match "NPU|AI Boost|Neural Processing"
} | Select-Object FriendlyName, Status, InstanceId
Write-Host "Diagnóstico terminado. Revisa el resultado localmente antes de compartirlo."
