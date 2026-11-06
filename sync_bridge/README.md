# Matick Sync Bridge v0.1 🛰️

**Puente de mensajes local, verificable y sin membresías adicionales obligatorias.** Forma parte del proyecto **Matick Studio LM Cloud**, producto propio independiente de LM Studio.

Este servicio **sí** permite enviar eventos entre agentes/clientes y recibirlos rápidamente mediante *long-polling* (sin esperar el siguiente ciclo horario). Guarda eventos/tareas en SQLite para consultas posteriores. **No** controla automáticamente aplicaciones de ChatGPT, Gemini Live o Claude Code y **no** las despierta por cambios en Google Docs. Para solicitar respuestas de modelos vía API hace falta habilitarlo y proporcionar API keys individuales, con facturación independiente cuando corresponda.

## Arranque Windows 11 (Python 3.11+)

Extrae el ZIP en una carpeta tuya, por ejemplo `C:\Users\TuUsuario\Documents\MatickSyncBridge`, no en Program Files. Desde PowerShell en esa carpeta:

```powershell
.\Start_Matick_Sync.ps1
```

Si Windows bloquea scripts, puedes abrir el archivo para inspeccionarlo y ejecutarlo desde un PowerShell con políticas adecuadas a tu equipo. Alternativa manual sin scripts:

```powershell
$env:MATICK_SYNC_TOKEN = ([Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)))
$env:PYTHONPATH = (Get-Location).Path
python -m matick_sync.server
```

> Los comandos CLI necesitan la misma variable `MATICK_SYNC_TOKEN` y el mismo `PYTHONPATH` de la consola que inició el puente. Con el script PowerShell, el servidor se abre en otro proceso y la ventana original puede usar el CLI. Guarda la clave solo en un gestor seguro, no en GitHub o Google Docs.

### Ejemplo local sin gastar API

```powershell
py -3 -m matick_sync.cli status
py -3 -m matick_sync.cli send all "Proyecto activo: Matick Studio LM Cloud"
py -3 -m matick_sync.cli watch --once
py -3 -m matick_sync.cli watch
```

La respuesta de `watch` se actualiza cuando un cliente autorizado envía un evento (espera máxima configurada: 20 segundos, normalmente se recibe inmediatamente). El puente funciona localmente incluso si no hay Internet.

### API HTTP local

| Método | Ruta | Autenticación | Qué hace |
|---|---|---|---|
| GET | `/health` | Pública | Indica que el proceso está vivo. |
| GET | `/v1/status` | Bearer | Identidad, API activada y modelos configurados. |
| POST | `/v1/events` | Bearer | Guarda mensaje y notifica a observadores (máx. 6000 caracteres). |
| GET | `/v1/poll?after=0&wait=20` | Bearer | Entrega eventos de forma inmediata si llegan, o espera. |
| POST | `/v1/tasks` | Solo Morlet + API habilitada | Una solicitud expresa a modelos elegidos, sin bucles. |
| GET | `/v1/tasks/{id}` | Solo Morlet | Estado y resultado de la tarea. |

Ejemplo JSON para `POST /v1/events`:

```json
{"recipient":"all","kind":"message","text":"Revisen Matick Cloud","client_id":"mensaje-001"}
```

Para conectar agentes externos manualmente, cada programa necesita un cliente HTTP que se autentique y haga `poll`/`POST` cuando esté ejecutándose. **El navegador abierto o un Google Doc no constituye un cliente de este puente.**

## API de modelos: opcional, desactivada por defecto

Solo si aceptas usar tus propias credenciales API (con posibles costes), antes de arrancar configura:

```powershell
$env:MATICK_SYNC_ENABLE_API = '1'
$env:MATICK_SYNC_MAX_TASKS = '3'   # tres tareas por cada arranque
$env:GEMINI_API_KEY = '<tu clave, solo en tu PC>'
$env:GEMINI_MODEL = '<modelo confirmado en tu cuenta>'
$env:ANTHROPIC_API_KEY = '<tu clave, solo en tu PC>'
$env:CLAUDE_MODEL = '<modelo confirmado en tu cuenta>'
$env:OPENAI_API_KEY = '<tu clave, solo en tu PC>'
$env:OPENAI_MODEL = '<modelo confirmado en tu cuenta>'
```

Las claves se transmiten **únicamente** a los endpoints HTTPS oficiales de cada proveedor. Las llamadas no incluyen herramientas para manipular tu PC o GitHub, y **no son la misma sesión** de tus apps ChatGPT, Gemini Live y Claude Code. Tu plan ChatGPT Plus no incluye automáticamente el crédito de la API.

Después inicia el bridge y solicita deliberadamente una tarea (1 llamada por agente indicado, sin reintentos):

```powershell
py -3 -m matick_sync.cli ask --agents gemini,claude "Propongan dos pruebas pequeñas para Matick Studio LM Cloud"
py -3 -m matick_sync.cli watch
```

Los nombres de modelos NO están fijados en el código: cámbialos según disponibilidad. El servidor limita las tareas API por arranque y no llama modelos a partir de mensajes recibidos, evitando círculos de gasto.

## Roles y permisos

En modo simple solo está disponible el rol `morlet`, con una clave de sesión. Para crear clientes distintos, define `MATICK_SYNC_TOKENS_JSON` con **claves únicas y largas** para `morlet`, `matick`, `gemini`, `claude` y `chatgpt`. La identidad se deriva de la clave autenticada, no de un campo suministrado por el cliente. Los agentes solo pueden enviar respuesta a Morlet o a `all`, no pueden lanzar tareas API.

**Seguridad:** solo escucha en `127.0.0.1`. Para conectar teléfono u otro equipo se necesita un túnel/proxy HTTPS autenticado y medidas adicionales; no abras el puerto HTTP directamente a internet. No recopila datos de salud. La base SQLite y sus mensajes quedan en `%LOCALAPPDATA%\MatickSyncBridge\events.db` en Windows; respáldala o elimínala manualmente cuando lo decidas.

## Google Drive y tareas periódicas

La bitácora del equipo sigue en [CHATS_Gemini_GPT.md](https://docs.google.com/document/d/18LMpu2VgfBSaYjX06-JtGcAwhYxdLxr8lEOFluWyQPE/edit). El bridge **no accede a Drive por sí solo** en v0.1; conectar Drive de forma automática requiere autorización OAuth explícita y gestión de cambios/duplicados. La automatización horaria que ya existe en ChatGPT sigue siendo independiente.

## Pruebas

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m unittest discover -s tests -v
```

Prueban el aislamiento por rol, autenticación, idempotencia, long-polling y el bloqueo de solicitudes de pago sin autorización. Se usa un agente simulado en pruebas; los endpoints reales de proveedores no se llaman.

**Limitaciones v0.1:** sin WebSocket multimedia, sin aplicación móvil ni APK, sin proceso Windows Service, sin OAuth Google Drive, sin conexión automática a las aplicaciones de chat, sin integración directa con el ejecutable DX12 y sin despliegue 24/7. Esto es una base de comunicación local real y segura, no una red de modelos permanente ya desplegada.
