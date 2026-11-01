
# Matick Studio LM · diagnóstico visual seguro y optimización propia

El proyecto [windows-optimization](https://github.com/topics/windows-optimization) de GitHub reúne herramientas de terceros con enfoques diferentes. Para Matick aprovechamos **únicamente las ideas generales** de diagnósticos, rendimiento medible y recuperación; no ejecutamos ni incluimos debloaters, hacks del registro, servicios desactivados, drivers ni utilidades externas.

## Síntoma: el launcher abre sin mostrar nada

En la versión anterior, `wWinMain` llamaba a `renderer.Init(window)` **antes** de `ShowWindow`. Si fallaba la creación del dispositivo o el swap chain DirectX 12, destruía la ventana sin mostrar su contenido. Además, la ventana no ofrecía un modo 2D de rescate.

## Corrección implementada

- Se crean controles Win32 y **se muestra la ventana primero**.
- Se intenta DirectX 12 posteriormente. Si falla, Matick **se mantiene abierto** y dibuja el fondo con Win32/GDI, sin DirectX 12.
- También hay recuperación desde un error de renderizado después del arranque.
- `MATICK_RENDERER=gdi` permite iniciar siempre en modo seguro sin tocar configuración del sistema.
- La composición DX12 se actualiza de forma menos frecuente porque el contenido GPU es estático. La mascota Win32 mantiene su animación.
- La sincronización GPU tiene un tiempo límite de dos segundos, evitando bloqueos indefinidos si se pierde el dispositivo.
- Se guarda una bitácora de arranque con HRESULT en `%LOCALAPPDATA%\MatickStudioLM\logs\render.log`.

## Arrancar en modo seguro

Extrae el ZIP portable de GitHub en una carpeta nueva (no encima de `C:\IA\Matick Studio LM`).

Abre PowerShell en esa carpeta:

```powershell
.\tools\start_matick_portable.ps1 -SafeMode
```

Si tu política de PowerShell impide ejecutar scripts, puedes iniciar el programa directamente desde la misma sesión, sin cambiar políticas globales:

```powershell
$env:MATICK_RENDERER = "gdi"
.\MatickStudioLM.exe
Remove-Item Env:MATICK_RENDERER -ErrorAction SilentlyContinue
```

Para probar el modo normal:

```powershell
.\tools\start_matick_portable.ps1
```

El estado de la interfaz se muestra dentro de la ventana: `DirectX 12 operativo` o `modo seguro GDI`.

## Qué significa una ventana visible

Que la ventana y sus controles aparezcan **no demuestra** que el motor de modelos funcione. La llamada `/health` solo comprueba la API, no que el modelo genere texto. Los problemas previos con el puerto 4321 pertenecen al proyecto local y requieren identificar qué servidor lo ocupa sin matar procesos de forma automática.

## Registro / errores

Abre el archivo `$env:LOCALAPPDATA\MatickStudioLM\logs\render.log` en Bloc de notas. Cada línea indica una fase (`WINDOW_VISIBLE`, `DX12_INIT_BEGIN`, `DX12_INIT_OK`, `DX12_FIRST_FRAME_OK`, `DX12_RENDER_FAILED_SWITCHING_TO_GDI`) y, si falló una llamada, su código HRESULT hexadecimal.

El script y el EXE **no modifican** Windows, el registro, antivirus, drivers, tareas programadas ni la versión local del usuario.

## Limitaciones de pruebas

Las pruebas automatizadas validan compilación Windows, contratos y ruta de modo seguro, pero una prueba completa de visibilidad real necesita el monitor y la GPU del usuario. El ejecutable compilado desde GitHub puede ser diferente al launcher de su carpeta `C:\IA\Matick Studio LM`; actualizar este repo no lo sobrescribe.
