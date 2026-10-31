# Auditar Matick Studio LM en MORLET-GAMING — edición 31/10/2026

## Qué verifica

El script **tools/auditar_matick_pc.py** inventaría **TODOS** los archivos de C:\IA\Matick Studio LM por ruta relativa y tamaño, sin alterar un solo archivo. Analiza con AST los archivos Python propios menores de 2 MB, valida JSON y estructura de mcp.json, detecta archivos grandes/modelos/CUDA y verifica el encabezado de un ejecutable PE x64 si está en rutas habituales. Solo calcula SHA-256 de archivos de hasta 16 MB de forma predeterminada y NO lee contenidos de archivos privados; --deep-hash permite cubrir grandes archivos no privados. No lanza servidores, modelos, MCP ni ejecutables.

También intenta conexión **solo a localhost** con el servidor Matick y LM Studio REST v1; puedes activar una consulta real de chat a tu modelo con --chat-smoke. Para la autenticación se utiliza MATICK_TOKEN del entorno, nunca un secreto en línea de comandos, y no se registra su valor.

## Descargar y ejecutar en PowerShell normal

Guarda el archivo auditar_matick_pc.py desde GitHub, preferentemente en Descargas. Desde PowerShell:

    py -3 "$env:USERPROFILE\Downloads\auditar_matick_pc.py" --root "C:\IA\Matick Studio LM"

Opciones:

    py -3 "$env:USERPROFILE\Downloads\auditar_matick_pc.py" --root "C:\IA\Matick Studio LM" --chat-smoke

Para una comprobación exhaustiva de hashes, que puede leer muchos GB y tardar:

    py -3 "$env:USERPROFILE\Downloads\auditar_matick_pc.py" --deep-hash

## Archivos de salida

Se crea una carpeta NUEVA dentro de Descargas: Matick_Auditoria_YYYYMMDD_HHMMSS.

- **Matick_Resultado_1_a_100.md**: calificación y observaciones. Comparte preferentemente solo este archivo.
- **Matick_Inventario_Completo.json**: un registro por archivo con tamaño, estado y SHA256 cuando se pueda; sus nombres pueden ser privados. Revisa antes de compartir.

El verificador **no instala nada, no modifica Matick Studio LM, no ejecuta scripts del proyecto y no envía inventarios**.

## La puntuación 1..100 NO es un certificado de funcionamiento integral

Las pruebas suman hasta 100 puntos: 25 inventario/errores, 12 sintaxis Python, 5 JSON, 8 MCP, 5 enlaces, 15 herramientas, 10 cabecera EXE y 20 pruebas API/inferencia local (total 100). Las pruebas no realizadas cuentan como **sin evidencia**, no como fallos demostrados.

Un 100 indica que todos esos controles concretos pasaron, pero NO garantiza ausencia de bugs, seguridad completa, rendimiento, DirectX12 activo, resolución de imágenes, agentes o estabilidad. Es imposible certificar el 100% de un software solo por analizar archivos. Para ello harían falta pruebas de UI y flujos end-to-end en la PC, con tu autorización.

## Cómo usar para mejoras

Antes de integrar en el proyecto local, comparar el reporte con la versión portable de Matick Cloud v1 y decidir qué módulos se transferirán. No copiar las carpetas CUDA, modelos, bibliotecas de terceros ni credenciales a GitHub. Cualquier fusión requiere respaldo y un ensayo separado.
