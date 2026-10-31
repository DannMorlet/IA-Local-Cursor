# Matick Studio LM ☁️ + DirectX 12

**Repositorio oficial del nuevo proyecto Matick Studio LM en la nube.** Es un producto independiente de LM Studio y no requiere instalar LM Studio para que su servidor de mensajes funcione.

> Estado: **vista previa 0.2 — chat ligero opcional**. Incluye un bus HTTP autenticado con SQLite, un proveedor HTTP de inferencia configurable, un ejecutable nativo DirectX 12 que puede enviar mensajes y un paquete portable de archivos permitidos. **No** incluye pesos/modelos ni un servidor cloud 24/7 desplegado, ni conexión real con ChatGPT, Alexa, reloj o un instalador final firmado.

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

## Bibliotecas centrales y herramientas MCP (integración inicial)

Se agregó [Matick ToolHub](integrations/toolhub/): un adaptador **opcional** de `@lmstudio/sdk` (SDK oficial de `lmstudio-js`) y un cliente MCP local `stdio` con registro `mcp.example.json`, descubrimiento de herramientas y autorizaciones explícitas. Revisa [guía de integración, ramas experimentales y seguridad](docs/INTEGRACION_LMSTUDIO_MCP.md).

- Compatible con la idea de **Matick Studio LM propio**: LM Studio no es requisito para la interfaz DX12 ni el servidor cloud.
- Los ocho MCP del respaldo GemCo están catalogados como **deshabilitados por defecto** y requieren que sus scripts existan en Windows.
- Las ramas de `lmstudio-js` son material de investigación; se integra una versión publicada del SDK sin copiar código experimental.
- El cliente MCP y SDK funcionan como un proceso Node separado; todavía falta el puente entre ese proceso y el ejecutable DX12 y la nube.

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
