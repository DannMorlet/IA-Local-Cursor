# Matick Studio LM — nube ligera y traslado seguro a MORLET-GAMING

## Objetivo

Terminar Matick Studio LM en **GitHub**, como base principal del proyecto. El inventario recibido de MORLET-GAMING reportó **2273 archivos fuente**, muchos de ellos encabezados y bibliotecas de CUDA, frente a un prototipo cloud mucho menor. No deducimos que todos los archivos locales sean funcionales.

**No copiar** `C:\IA\Matick Studio LM` al repositorio, ni su carpeta `CUDA`, ni `models`, `node_modules`, entornos, artefactos de compilación, pesos, drivers, logs o credenciales. Toda la distribución se genera con una *lista de archivos permitidos*, no copiando carpetas completas.

## Lo que sí funciona en esta iteración

- Windows `MatickStudioLM.exe` nativo con Direct3D 12, tablero y mascota vectorial provisional.
- El botón **Enviar** hace una petición **autenticada** `POST /v1/chat` en un hilo de trabajo; muestra la respuesta en el panel central si hay un proveedor listo.
- La API Python sin dependencias externas conserva los eventos, agrega `/v1/capabilities` y chat con un **motor remoto o local compatible con OpenAI Chat Completions**, configurado por variables de entorno.
- Windows utiliza únicamente WinHTTP y Windows SDK, sin incrustar Node ni LM Studio.
- ToolHub Node utiliza `@lmstudio/sdk` **solo si se instala por separado**. Los ocho MCP del catálogo permanecen inactivos por defecto.

## Lo que no está listo (no simularlo en la interfaz)

- No se ha desplegado Matick Cloud 24/7 ni configurado un proveedor real de inferencia con credenciales.
- La mascota definitiva, el gestor de archivos, agentes autónomos, acceso remoto al PC y conexiones reales con Alexa, ChatGPT, Galaxy Fit 3 y Matick Codex quedan pendientes.
- La conexión MCP no se ejecuta desde la UI DX12 ni se concede control sin consentimiento.
- La aplicación aún no tiene instalador firmado, panel responsive ni sincronización automática entre equipos.

## Ejecutar un proveedor y hacer una primera prueba

`MATICK_MODEL_BASE_URL` apunta a un servidor de inferencia **OpenAI-compatible** que tú administras, no necesariamente LM Studio. Si deseas usar un modelo en el mismo host que Python, ejemplo con puerto 1234:

```powershell
cd cloud
$env:MATICK_TOKENS_JSON='{"windows-dx12":"CAMBIA_ESTO_POR_UN_TOKEN_DE_AL_MENOS_16_CARACTERES"}'
$env:MATICK_MODEL_BASE_URL='http://127.0.0.1:1234/v1'
$env:MATICK_MODEL_ID='ID_EXACTO_DEL_MODELO_CARGADO'
python -m matick_cloud
```

En otra ventana del mismo equipo:

```powershell
$env:MATICK_TOKEN='EL_MISMO_TOKEN_QUE_WINDOWS_DX12'
$env:MATICK_CLOUD_URL='http://127.0.0.1:8787'
.\MatickStudioLM.exe
```

No reutilices tokens de ejemplo; asigna un token nuevo y único. El SDK `lmstudio-js` tiene un protocolo WebSocket distinto; este endpoint usa la API HTTP estilo OpenAI, por lo que son **adaptadores diferentes**.

**Para nube real**, configura HTTPS, credenciales de backend en secreto de despliegue, un dominio autorizado, SQLite en volumen persistente y límites de solicitudes; GitHub Actions compila, pero **no hospeda tu API constantemente**.

## Traslado sin destruir la versión local

1. Descarga el ZIP `MatickStudioLM-Windows-x64` de GitHub Actions. Se empaqueta mediante `tools/package_portable.ps1`, que copia únicamente el `.exe`, archivos Python esenciales de API, scripts ToolHub sin `node_modules`, ejemplos y documentación.
2. Descomprime en una carpeta propia, por ejemplo Descargas\Matick_GitHub_Prueba. El proyecto de `C:\IA\Matick Studio LM` se deja intacto.
3. Ejecuta el preflight en PowerShell desde la carpeta descomprimida: `.\tools\prepare_local_transfer.ps1`. No copia nada, solamente indica las rutas.
4. Si decides preparar una revisión dentro del proyecto local, ejecuta **manualmente** `.\tools\prepare_local_transfer.ps1 -Stage`. Verifica manifiesto SHA256 y crea una carpeta nueva `C:\IA\Matick Studio LM\_Matick_GitHub_Revision`; se niega a reemplazarla si existe.
5. No borrar ni sustituir programas ejecutables del proyecto local hasta que la comparación, los modelos y la UI pasen pruebas en esa PC.

Si falla una dependencia, el paquete informa qué falta. **No puede prometer compatibilidad absoluta sin ejecutar ambas versiones en MORLET-GAMING.**

## Recursos omitidos

Nunca copiar a la distribución portátil: `CUDA/`, `models/`, `modelos/`, `weights/`, `node_modules/`, `.venv/`, `bin/`, `obj/`, `build/`, `dist/`, `secretos/`, `mcp.json` con rutas y tokens personales. Solo `mcp.example.json` sin credenciales.

### Versiones y licencias

Código propio: Apache 2.0 según el repositorio. `lmstudio-js` se integra como paquete opcional npm MIT; no se redistribuye el SDK ni se incorporan sus ramas experimentales.
