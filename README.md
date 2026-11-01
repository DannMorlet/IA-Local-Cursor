# Matick Studio LM ☁️ + DirectX 12

**Repositorio oficial del nuevo proyecto Matick Studio LM en la nube.** Es un producto independiente de LM Studio y no requiere instalar LM Studio para que su servidor de mensajes funcione.

> Estado: **Matick Studio LM Cloud v1.0 — software ejecutable y comprobable**. Incluye un bus HTTP autenticado con SQLite, un proveedor HTTP de inferencia configurable, un ejecutable nativo DirectX 12 que puede enviar mensajes y un paquete portable de archivos permitidos. **No** incluye pesos/modelos, despliegue cloud 24/7, conexión real con ChatGPT/Alexa/reloj, agente Codex que ejecuta código ni un instalador firmado.

## Instalador Windows x64 con desinstalación segura (v1.0.1)

**Matick puede instalarse como programa independiente** desde un ZIP de GitHub Actions que incluye `MatickStudioLM-v1.0.1-x64-Setup.exe`. El instalador incluye Python 3.12.10 embebido (fuente oficial Python.org con SHA256 fijo), Matick Core y la interfaz nativa DirectX 12. **No requiere instalar Python, Node ni LM Studio** para abrirse y arrancar la API local.

Instalación por usuario en `%LOCALAPPDATA%\Programs\Matick Studio LM Cloud`, con desinstalador registrado en *Aplicaciones instaladas*. Conserva bases SQLite, registros, modelos y tu desarrollo `C:\IA\Matick Studio LM`. **No incluye modelos entrenados:** el chat requiere configurar un proveedor de inferencia.

[Guía del instalador y desinstalación](docs/INSTALADOR_WINDOWS_X64.md).

## Ventana DirectX 12: modo seguro si el launcher aparece vacío

La versión Windows abre la interfaz **antes** de iniciar la GPU. Si DirectX 12 falla, utiliza el dibujado básico de Windows (GDI) en vez de cerrarse con una ventana vacía. El log local `%LOCALAPPDATA%\\MatickStudioLM\\logs\\render.log` muestra la fase y el error HRESULT. Puedes arrancar con `.\\tools\\start_matick_portable.ps1 -SafeMode` sin modificar el registro ni desactivar servicios. [Guía de diagnóstico y optimización de bajo riesgo](docs/DIAGNOSTICO_RENDER_WINDOWS.md).

## Auditoría de MORLET-GAMING: puntuación 1..100

Para verificar la instalación **local** de `C:\IA\Matick Studio LM`, se incluye el [auditor Python solo lectura](tools/auditar_matick_pc.py) y un [lanzador de Windows](tools/Auditar_Matick_PC.cmd). Inventaría todos los archivos por metadatos, analiza sintaxis Python/JSON, MCP, cabecera PE y conectividad local opcional. Guarda reporte Markdown y un JSON de inventario en **Descargas**, nunca dentro del proyecto. La calificación mide verificaciones superadas, no garantiza el 100 % del funcionamiento.

[Instrucciones y límites de la auditoría](docs/AUDITORIA_PC_1_A_100.md).

## Matick Studio LM Cloud v1.0 — Work y modelos

**Panel de trabajo tipo Codex (inspiración visual, no código de OpenAI):** iniciar servidor Python, abrir `http://127.0.0.1:8787/app`. Introducir el token del rol Windows o Studio: solo se guarda en la memoria de la pestaña y no se escribe en disco del navegador. Incluye trabajo/tablero persistente, chat, administrador de modelos y estado de herramientas.

**REST v1 de LM Studio (opcional):** configura `MATICK_REST_V1_URL=http://127.0.0.1:1234` cuando tengas el servidor 0.4+ iniciado. Desde Matick Work podrás consultar modelos, seleccionar uno, ajustar contexto, temperatura, Top P, Top K, Flash Attention, batch, tokens de salida, cargar y descargar de RAM. Los parámetros se guardan en SQLite de Matick. La inferencia usa `POST /api/v1/chat` del proveedor. Matick continúa siendo independiente de LM Studio: sin adaptador, funciona el tablero y el bus; también existe proveedor alternativo OpenAI-compatible.

**Descarga de nuevos modelos:** se solicita con `POST /v1/models/download`; está desactivada por defecto y solo se permite al habilitar `MATICK_ALLOW_MODEL_DOWNLOADS=1` en el servidor, para evitar consumir GB inesperadamente. Los modelos quedan en el almacenamiento del proveedor, nunca en el repositorio.

[Guía de API REST v1 y parámetros](docs/REST_V1_MODELOS.md).

## 🥭 Versión ligera para GitHub y traslado posterior a tu PC

**La nube de GitHub es el desarrollo principal**, distinto de la versión incompleta de `C:\IA\Matick Studio LM`. No copiamos sus 2273 archivos ni sus carpetas CUDA: evitamos trasladar encabezados, controladores, librerías de terceros, pesos, `node_modules` y datos sensibles.

- **Chat real, condicionado:** el backend Python incluye `POST /v1/chat`, protegido por token de cliente, y `GET /v1/capabilities`. Se conecta a un proveedor OpenAI-compatible cuando tú lo configuras. No inventa respuestas si no está instalado/configurado el modelo.
- **Cliente Windows:** el botón Enviar usa WinHTTP de Windows con token `MATICK_TOKEN`. Requiere `MATICK_CLOUD_URL` (por defecto local en puerto 8787). HTTPS obligatorio fuera del equipo local.
- **Portabilidad:** GitHub Actions crea `MatickStudioLM-Windows-x64-Portable` con `.exe`, backend Python mínimo, ToolHub **sin dependencias instaladas** y un manifiesto SHA256.
- **Migración no destructiva:** `tools/prepare_local_transfer.ps1` en modo normal **no copia nada**. Con `-Stage` crea una carpeta NUEVA separada y verifica hashes, sin cambiar tu versión local.

📚 [Plan de traslado seguro y guía de inicio](docs/PLAN_CLOUD_A_PC.md).

## Diseño del tablero aprobado — vista DX12

La referencia visual que aprobaste se está trasladando a la aplicación nativa: navegación oscura a la izquierda, zona de trabajo clara en el centro, tarjetas de seis frentes y modelos, y mascota a la derecha. Consulta [la especificación visual](docs/UI_REFERENCIA_MATICK.md).

**Estado del prototipo visual:** los paneles y navegación de demostración están implementados; la mascota es un dibujo vectorial provisional que parpadea, **no todavía tu recurso original animado**. El botón Enviar consulta `/v1/chat` con un token de sesión y muestra la respuesta **si un proveedor está configurado**. No ejecuta herramientas ni controla el equipo automáticamente. Las conexiones de Alexa, ChatGPT y el reloj se marcan como pendientes hasta ser verificadas.

## Matick Core y herramientas propias MCP

**Matick Studio LM es software nuevo e independiente**: API Matick REST v1, interfaz DirectX 12 y Matick Work, datos SQLite y herramientas desarrolladas dentro del proyecto. No es una distribución renombrada de LM Studio.

**Nuevo [Matick MCP Bridge](integrations/matick-mcp/matick_mcp.py):** servidor MCP `stdio` original, escrito en Python estándar. Permite a aplicaciones compatibles (incluido LM Studio si tú lo decides) consultar Matick sin incorporar ni copiar su código. Ofrece `matick_health`, `matick_capabilities`, `matick_models`, `matick_tasks`; la creación de tareas y el chat requieren activar permisos explícitos.

**[Matick ToolHub](integrations/toolhub/):** cliente de nuestra propia API Matick y cliente MCP genérico. Su paquete Node no tiene dependencias de proveedores de IA; ni el SDK de LM Studio ni bibliotecas CUDA forman parte del núcleo.

**[Guía oficial de independencia e integración MCP](docs/MATICK_INDEPENDENCIA_Y_MCP.md)** · [mcp.example.json](integrations/matick-mcp/mcp.example.json).

Los proveedores de inferencia externos siguen siendo opcionales, y **Matick todavía no ejecuta modelos mediante un runtime de inferencia propio**. Sus marcas se mencionan únicamente para describir compatibilidad.

## Arquitectura

| Componente | Dónde corre | Responsabilidad |
| --- | --- | --- |
| `MatickStudioLM.exe` | Windows 11 | Ventana nativa Direct3D 12, estado de API, chat autenticado y respuesta si hay proveedor. |
| `matick_cloud` | Servidor / contenedor en la nube | API HTTP de eventos y chat con proveedor configurable, sin dependencias extra. |
| Matick Codex / Chat / Reloj / Alexa / ChatGPT | Integraciones futuras | Clientes separados con identidad y permisos propios. |
| Modelo de IA | Servicio de inferencia configurable | La API llama un modelo por HTTP cuando está configurado; **no** almacena ni ejecuta pesos por su cuenta. |

**Importante:** GitHub aloja el código y puede compilar el `.exe` con Actions, pero **no** es un host persistente para el servidor cloud. Para acceso remoto, desplegar el contenedor en un host propio y configurar **HTTPS** con un proxy.

## Empezar: servidor (Python estándar)

Requiere Python 3.11 o superior.

```powershell
cd cloud
$env:MATICK_TOKENS_JSON='{"matick-studio-lm":"cambia-token-studio","matick-chat":"cambia-token-chat"}'
$env:MATICK_HOST="127.0.0.1"
$env:MATICK_PORT="8787"
python -m matick_cloud
```

Para verificar:

```powershell
Invoke-RestMethod http://127.0.0.1:8787/health
```

Prueba de comunicación autenticada en otra terminal:

```powershell
cd cloud
$env:MATICK_CLOUD_URL="http://127.0.0.1:8787"
$env:MATICK_TOKEN="cambia-token-studio"
python -m matick_cloud.client send matick-chat mensaje '{"texto":"Hola desde Studio"}'
$env:MATICK_TOKEN="cambia-token-chat"
python -m matick_cloud.client inbox
```

Los tokens de ejemplo son **solo para desarrollo local**. No se deben utilizar tal cual en internet.

## Ejecutable Windows DirectX 12

Compila con **Windows SDK + Visual Studio 2022 C++ Build Tools + CMake**:

```powershell
cmake -S windows -B out/build -G "Visual Studio 17 2022" -A x64
cmake --build out/build --config Release
.\out\build\Release\MatickStudioLM.exe
```

El cliente utiliza `MATICK_CLOUD_URL` para consultar `/health` y `MATICK_TOKEN` para enviar mensajes al endpoint `/v1/chat` cuando el backend tiene un modelo configurado. El valor por defecto de la URL es `http://127.0.0.1:8787`. Para nube remota se requiere **HTTPS**.

GitHub Actions (pestaña **Actions**) también genera el artefacto `MatickStudioLM-Windows-x64` si la compilación concluye correctamente.

## Despliegue del servidor en un contenedor

```bash
docker build -t matick-studio-lm-cloud ./cloud
docker run --rm -p 127.0.0.1:8787:8787 \
  -e MATICK_TOKENS_JSON='{"matick-studio-lm":"TOKEN_LARGO_ALEATORIO"}' \
  -v matick-data:/data matick-studio-lm-cloud
```

El ejemplo solo enlaza el puerto en localhost. Para producción: reverse proxy TLS, credenciales distintas por cliente, límites de peticiones, backups, monitoreo y volumen persistente. El servicio usa SQLite y está pensado para **una sola instancia**; no se presenta como una plataforma multiinstancia escalable.

## Organización del proyecto

- `cloud/`: servidor, cliente de prueba, contenedor y pruebas automatizadas.
- `windows/`: interfaz de Windows nativa Direct3D 12.
- `docs/ARCHITECTURA.md`: topología y seis áreas de implementación.
- `docs/SEGURIDAD.md`: límites y prácticas antes de publicar.
- `.github/workflows/ci.yml`: pruebas cloud y compilación x64 de Windows.

## Estado de integraciones

| Integración | Estado |
| --- | --- |
| API de mensajes bidireccionales entre roles permitidos | **Implementada** (polling + SQLite) |
| Identidad por token de cada rol | **Implementada** (MVP) |
| Windows `.exe` nativo DirectX 12 | Renderizado, formulario y llamada de chat implementados; validar en la GPU del usuario |
| ChatGPT ↔ Matick Studio LM | Contrato preparado, **no conectado** |
| Alexa / Matick Reloj / Matick Codex / Matick Chat | Contrato preparado, **no conectados** |
| Inferencia de modelos IA en la nube | Adaptador HTTP opcional implementado; **sin modelo ni host desplegados** |
| Despliegue 24/7 y dominio | **No realizado** |

**Migración:** el proyecto anterior `IA-Local-Cursor / GemCo-Joystick` quedó preservado en la rama de respaldo `backup/ia-local-cursor-antes-matick-studio-lm-20261030`. Esta rama `main` comienza de cero, sin reaprovechar el MCP anterior.

Licencia: Apache-2.0 (se conserva el archivo LICENSE del repositorio).
