# Comparar Matick Studio LM local vs GitHub sin modificar el proyecto

La carpeta del proyecto local de referencia es **`C:\IA\Matick Studio LM`**. La versión cloud está en `DannMorlet/IA-Local-Cursor` (rama `main`).

Este comparador es **solo lectura dentro de la carpeta local**. No ejecuta ni compila el proyecto de Windows, no abre tu `.exe`, no inicia modelos, no usa MCP, no transfiere archivos privados y no sube nada del equipo a GitHub. Solo solicita el árbol de archivos públicos a GitHub para comparar hashes de archivos fuente pequeños, omitiendo binarios, modelos, credenciales, `mcp.json` y otras carpetas que puedan contener información privada.

## Paso A. Probar el ejecutable de GitHub de manera independiente

1. Entra al [último workflow aprobado](https://github.com/DannMorlet/IA-Local-Cursor/actions/runs/41233935282).
2. En `Artifacts`, descarga **MatickStudioLM-Windows-x64**.
3. Extrae el ZIP en una carpeta **separada**, por ejemplo `%USERPROFILE%\Downloads\Matick_GitHub_Prueba`, fuera de `C:\IA\Matick Studio LM`.
4. Ejecuta `MatickStudioLM.exe`. Comprueba que abra una ventana DirectX 12, se vean los tres paneles, la mascota provisional parpadee y la ventana cierre sin errores.
5. Que aparezca «API cloud: desconectada» es normal si no hay un servicio local iniciado en el puerto 8787. Ese indicador no comprueba que ChatGPT, Alexa o el motor IA estén operativos.

> Los ejecutables son prototipos, no instaladores. Si Windows advierte sobre un binario sin firmar, inspecciona su procedencia. No desactives SmartScreen ni protecciones del sistema.

## Paso B. Obtener comparación de código desde tu PC

En **PowerShell** abre una ventana normal (no administrador). Requiere Python 3.11+; tu Python 3.15 es válido.

```powershell
$script = Join-Path $env:TEMP "comparar_matick_solo_lectura.py"
Invoke-WebRequest "https://raw.githubusercontent.com/DannMorlet/IA-Local-Cursor/main/tools/compare_local.py" -OutFile $script
py -3 $script --local "C:\IA\Matick Studio LM" --output "$env:USERPROFILE\Downloads\Matick_Comparacion_PC_Github.md"
```

Revisa el script [aquí](../tools/compare_local.py) antes de ejecutarlo. Puedes modificar la línea `py -3` a la ruta completa de tu intérprete Python si tu equipo no reconoce `py`.

El informe se guarda en **Descargas**, no en el proyecto. Revisa su contenido antes de compartirlo; incluirá **rutas relativas de los archivos de código**, pero no código fuente, variables de entorno ni contenido de configuraciones privadas.

## Paso C. Comparación de capacidades

Una vez que compartas el archivo `Matick_Comparacion_PC_Github.md`, podremos revisar qué componentes conviene trasladar primero. La presencia de archivos no demuestra funcionamiento: la comparación inicial se limita a código y la prueba manual del ejecutable.

Prioridades sugeridas: mantener la mascota original y el renderizado DX12 del equipo; aprovechar la API cloud probada de GitHub, evaluar ToolHub/MCP sin arrancar sus servidores automáticamente, y unir componentes con un contrato claro y permisos.

## Problemas frecuentes

- **La ruta no existe:** asegúrate de que la carpeta local sea exactamente `C:\IA\Matick Studio LM`.
- **No hay Python:** instala o usa el Python que ya tengas, sin modificar tu entorno existente.
- **Error 403 de GitHub:** se alcanzó el límite público de solicitudes; volver a intentar más tarde.
- **Archivos diferentes por formato Windows:** el informe distingue diferencias CRLF/LF del contenido real.
- **Muchos GB de modelos:** no se inspeccionan. Hay límite por archivo y límite global de lectura para evitar cargar recursos.
- **Resultado incompleto:** el programa indica archivos omitidos y no pretende comparar todos los recursos binarios.

**Nunca ejecutar scripts arbitrarios de tu carpeta local para «comprobar que funcionan» sin revisarlos previamente.**
