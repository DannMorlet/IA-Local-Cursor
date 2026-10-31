# Matick Studio LM v1.0 · API REST y modelos

Matick es una aplicación propia con servidor Python sin dependencias adicionales, interfaz nativa DirectX 12 y panel web de trabajo. La API REST v1 de **LM Studio >= 0.4.0** es un conector **opcional** (no el motor de Matick). Documentación oficial: https://lmstudio.ai/docs/developer/rest

## Inicio rápido en Windows 11

Terminal A: inicia LM Studio y el servidor de desarrollador (`lms server start`).

Terminal B, desde `cloud` dentro del ZIP portable:

```powershell
$token = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24))
$env:MATICK_TOKENS_JSON = "{`"windows-dx12`":`"$token`",`"matick-studio-lm`":`"$( [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24)) )`"}"
$env:MATICK_REST_V1_URL = "http://127.0.0.1:1234"
$env:MATICK_HOST = "127.0.0.1"
$env:MATICK_DB_PATH = Join-Path $env:TEMP "matick-v1-demo.db"
$env:MATICK_TOKEN = $token
py -3 -m matick_cloud
```

Abre `http://127.0.0.1:8787/app`; el token que acabas de generar está en la variable `$token` de Terminal B. Cópialo al formulario de conexión. Para iniciar `MatickStudioLM.exe` también necesitas una terminal con `MATICK_TOKEN` y `MATICK_CLOUD_URL` (no se guardan en el ejecutable).

Si tu versión de PowerShell no admite `[Convert]::ToHexString`, genera tokens aleatorios con Python, no uses contraseñas de ejemplo.

## Rutas propias Matick (Bearer token requerido)

| Método | Ruta | Función |
| --- | --- | --- |
| GET | `/health` | Salud del servidor sin token |
| GET | `/app` | Interfaz Work en navegador; solicita token |
| GET | `/v1/status` | Rol autenticado |
| GET | `/v1/capabilities` | Capacidades implementadas/configuradas |
| GET | `/v1/models` | Catálogo del REST v1 conectado, instancias en RAM |
| GET | `/v1/models/settings` | Modelo elegido y parámetros persistidos |
| POST | `/v1/models/settings` | Seleccionar modelo y guardar parámetros |
| POST | `/v1/models/load` | Cargar modelo conocido; configurar contexto, batch y KV |
| POST | `/v1/models/unload` | Descargar una instancia de RAM |
| POST | `/v1/models/download` | Solicitar descarga grande, requiere opt-in |
| POST | `/v1/chat` | Inferencia con REST v1 activo o proveedor alternativo |
| GET | `/v1/tasks` | Tablero de tareas persistentes |
| POST | `/v1/tasks` | Crear tarea |
| POST | `/v1/tasks/status` | Marcar por hacer/en curso/terminado |
| GET/POST | `/v1/events` | Mensajería por roles de Matick |

Se mantienen la autenticación por rol y SQLite. **Solo** roles `windows-dx12` y `matick-studio-lm` pueden cambiar modelos/tareas; otros roles autenticados consultan información, no ejecutan cambios.

## Ejemplo de carga

```powershell
$headers = @{ Authorization = "Bearer $env:MATICK_TOKEN" }
Invoke-RestMethod http://127.0.0.1:8787/v1/models -Headers $headers
$payload = @{ model='google/gemma-4-e2b'; params=@{
  context_length=4096; eval_batch_size=256; flash_attention=$true;
  offload_kv_cache_to_gpu=$true
}} | ConvertTo-Json -Depth 4
Invoke-RestMethod -Uri http://127.0.0.1:8787/v1/models/load -Method Post -Headers $headers -ContentType 'application/json' -Body $payload
```

El identificador debe existir en el catálogo del proveedor, no asumas que `google/gemma-4-e2b` es el ID exacto. Primero lista modelos.

## Parámetros validados

Generación: `temperature` 0..1, `top_p` 0..1, `top_k` 1..500, `min_p` 0..1, `repeat_penalty` 0.5..2, `max_output_tokens` 16..8192, `context_length` 512..65536 y `reasoning` pendiente de exponer.

Carga: `context_length` 512..65536, `eval_batch_size` 16..4096, `num_experts` 1..512, `flash_attention` booleano y `offload_kv_cache_to_gpu` booleano. Algunos modelos/motores no admiten todos los valores y devolverán un error real.

## Seguridad y límites de v1

- Nunca insertar contraseñas o claves en `mcp.json` público ni en GitHub.
- REST v1 upstream solo acepta HTTP por loopback o HTTPS externo con token; no se aceptan URLs arbitrarias en solicitudes del cliente ni redirecciones.
- No hay acceso a control de PC, permisos remotos MCP, ejecución de comandos ni sincronización de escritorio.
- `Matick Codex` no ejecuta código automáticamente aún: **Trabajo** es una cola de tareas persistente; el sistema distingue tareas de agentes operativos.
- La mascota vectorial del panel es provisional. La original del usuario no está empaquetada.
- El backend está pensado para instancia única. Antes de un despliegue público: proxy HTTPS, gestión de secretos, limitación de peticiones y almacenamiento protegido.
- La instalación portable contiene fuentes ligeros, servidor y EXE; no contiene modelos, CUDA, SDKs ni `node_modules`.
