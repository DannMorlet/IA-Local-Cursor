# Arranque Windows x64 1.2 — 2026-11-03

## Procedencia y coordinación

Base main 72a4178. Se consumió una copia fija del PR #58 hasta 3603dd9, sin escribir en su rama ni fusionar PR. Este complemento se revisa en rama separada. #56 aporta guardas de directorio y entorno, incorporadas y ampliadas. #47 contiene DPI/manifiesto y cambia la política a GDI por defecto; no se incorporó para conservar DX12 primero. DPI de #47 sigue pendiente.

## Archivo entregado

Inspección estática, sin ejecutar: PE32+ AMD64, GUI, 318464 bytes, SHA256 d2d81497c040f38c28041436d62896298e46a4a674b9526d21ccef4db33d1c52. Authenticode: NotSigned. Versión 1.0.0; OriginalFilename MatickStudioLM.dll. Es un apphost .NET que referencia MatickStudioLM.dll, no una distribución autónoma ni código fuente. No importa directamente d3d12.dll: eso no descarta carga dinámica desde dependencias, pero tampoco prueba DX12. Coincide exactamente con el EXE anterior de la instalación local. La instalación local tiene fuente C# y dependencias .NET8/CefSharp/Vortice; eso es un producto distinto del launcher C++ del repo. No se ejecutó el adjunto ni se atribuye a él el código reconstruido.

## Cambios

Launcher reconstruido de C++: versión PE 1.2.0.0, rechazo de compilación x86, runtime MSVC estático, DX12 primero y fallback GDI existente. Backend empaquetado como proceso hijo limitado por Job Object, no servicio registrado de Windows. Si existe App/runtime y App/cloud, el EXE de la raíz usa ese paquete conservando las fuentes, modelos y dependencias anteriores. El script no fuerza URL externa por defecto; conserva entorno y directorio. Diagnósticos de bootstrap visibles y salud exige identidad Matick y proceso hijo activo. Logs en %LOCALAPPDATA%/MatickStudioLM/logs.

Se corrigió fuga real SQLite: context managers transaccionales no cierran las conexiones; closing conserva transacciones y locks y libera los archivos en Windows.

## Validación y límites

Compilación MSVC x64 local. Pruebas funcionales del script en PowerShell5.1 y7, ejecutable de prueba, rutas con espacios, URL opcional y restauración. Paquete propio: GDI solicitado, proceso vivo, /health1.2.0, seis recursos HTTP y cierre del hijo; evidencia de log, sin inspección visual del monitor. 26 pruebas API/tareas/REST con Python3.12 embebido aprobadas. Las siete pruebas del motor con shebang se omiten en Windows y corresponden a Linux CI, no a inferencia real.

La copia local se instala en App; los dos EXE previos se respaldan antes de reemplazar. Generados bin/obj y tst.txt vacío se trasladan al respaldo, sin borrarlos. Los pesos existentes conservan hash. No se certifican RTX5060, DX12 físico ni pesos reales. El runtime llama.cpp pertenece al trabajo de #58: si no está instalado, se muestra su ausencia. No equivale a que todas las funciones históricas C# estén portadas.
