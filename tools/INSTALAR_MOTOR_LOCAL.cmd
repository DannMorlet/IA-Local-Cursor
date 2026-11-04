@echo off
setlocal
cd /d "%~dp0"
echo MATICK STUDIO LM - Instalador de motor local GGUF
echo Se descargara llama.cpp oficial de GitHub con verificacion SHA256.
echo No se instalaran controladores ni se borraran modelos.
echo.
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0install_llamacpp_engine.ps1"
if errorlevel 1 (
 echo.
 echo ERROR: la instalacion no ha terminado. Revisa el texto de arriba.
) else (
 echo.
 echo Instalacion finalizada o cancelada sin cambios.
)
pause
endlocal
