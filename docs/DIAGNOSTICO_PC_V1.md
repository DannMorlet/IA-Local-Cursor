# Diagnóstico Matick Studio LM para MORLET-GAMING

La versión principal de GitHub contiene el archivo **[tools/diagnostico_matick_pc_v1.py](../tools/diagnostico_matick_pc_v1.py)**, escrito en Python estándar sin bibliotecas de terceros. Está diseñado para revisar el proyecto **`C:\IA\Matick Studio LM`** sin copiar, borrar, instalar ni ejecutar sus archivos.

## Uso seguro (PowerShell)

Descarga primero el script y examínalo:

```powershell
$origen = "https://raw.githubusercontent.com/DannMorlet/IA-Local-Cursor/main/tools/diagnostico_matick_pc_v1.py"
Invoke-WebRequest -Uri $origen -OutFile "$env:USERPROFILE\Downloads\Matick_Diagnostico_PC_v1.py"
py -3 "$env:USERPROFILE\Downloads\Matick_Diagnostico_PC_v1.py" --ruta "C:\IA\Matick Studio LM"
```

Generará **tres archivos fuera de tu proyecto** en `Descargas\Matick_Diagnostico_PC`: `Matick_Diagnostico_Informe.md`, `Matick_Diagnostico_Resumen.json` y `Matick_Inventario_Completo.json`.

El inventario enumera *todos* los archivos encontrados —incluidos modelos y bibliotecas grandes— pero **no abre ni calcula hashes de esos archivos grandes**; solo obtiene nombres, tamaños y extensiones. Se comprueba sintaxis Python y un conjunto seguro de JSON propios, y formato PE básico de EXE (sin ejecutarlos). Los archivos `mcp.json` y `.env` se cuentan, pero no se lee su contenido. No se siguen symlinks ni junctions.

## Diagnóstico ampliado (opt-in)

```powershell
# Comprueba únicamente GET local a los puertos 8787 y 1234:
py -3 "$env:USERPROFILE\Downloads\Matick_Diagnostico_PC_v1.py" --red

# ATENCIÓN: esto sí ejecuta el código unittest presente en el proyecto:
py -3 "$env:USERPROFILE\Downloads\Matick_Diagnostico_PC_v1.py" --pruebas --red
```

**Importante:** `--pruebas` ejecuta el código del repositorio en tu equipo. Úsalo solo después de revisar que `cloud/tests` provenga de tu propio proyecto y sea confiable. No inicia automáticamente modelos, ni modifica el EXE, ni desactiva antivirus.

## Qué significa la puntuación

La salida da un **índice de preparación de 1 a 100** con pesos publicados en el propio script, junto con un porcentaje de **cobertura de comprobaciones**.

No es una medición objetiva de «qué porcentaje del programa funciona». Un archivo existente, una sintaxis correcta y una API respondiendo no certifican que se use correctamente una RTX 5060, que DirectX 12 dibuje bien o que ChatGPT, Alexa y Matick Reloj estén conectados.

Para certificar funciones específicas se requieren pruebas de comportamiento con tu hardware y proveedores reales. No se puede garantizar ausencia de errores por un escaneo de archivos.

**Privacidad:** solo comparte el archivo `Matick_Diagnostico_Informe.md` después de revisarlo. El inventario completo contiene rutas relativas y nombres privados.
