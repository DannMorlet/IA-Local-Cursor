@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Auditoria Matick Studio LM - MORLET-GAMING
echo.
echo ==============================================
echo  Auditoria Matick Studio LM ^(solo lectura^)
echo  Carpeta: C:\IA\Matick Studio LM
echo ==============================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0auditar_matick_pc.py" --root "C:\IA\Matick Studio LM" %*
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python "%~dp0auditar_matick_pc.py" --root "C:\IA\Matick Studio LM" %*
  ) else (
    echo ERROR: No encuentro Python. Instala Python 3.11 o superior.
    pause
    exit /b 1
  )
)
if errorlevel 1 echo La auditoria no se pudo completar. Revisa el mensaje anterior.
echo.
echo El reporte, cuando termina correctamente, se guarda en Descargas.
echo No se modifico ningun archivo del proyecto.
pause
