# Matick Studio LM ☁️ + DirectX 12

**Repositorio oficial del nuevo proyecto Matick Studio LM en la nube.** Es un producto independiente de LM Studio y no requiere instalar LM Studio para que su servidor de mensajes funcione.

> Estado: **MVP de dirección v0.2.0**. El bus HTTP/SQLite aplica rutas por rol, permite a Matick Studio LM y ChatGPT dirigir eventos a varios destinatarios explícitos, y ofrece un receptor de estatus de solo lectura para Matick Pet. Los adaptadores de Alexa, ChatGPT, Matick Chat, Matick Codex, Matick Reloj y la mascota siguen pendientes; el cliente Windows aún solo verifica `/health`.

## Arquitectura

| Componente | Dónde corre | Responsabilidad |
| --- | --- | --- |
| `MatickStudioLM.exe` | Windows 11 | Ventana nativa y renderizado **Direct3D 12**. Comprueba conectividad con el servicio cloud. |
| `matick_cloud` | Servidor / contenedor en la nube | API HTTP y entrega de mensajes entre clientes autenticados. |
| ChatGPT / Matick Chat / Matick Codex / Matick Reloj / Alexa | Integraciones futuras | Adaptadores separados con identidad y permisos propios. |
| Matick Pet | ChatGPT Work | Destino de `status.snapshot`; la actualización automática de la mascota requiere un adaptador pendiente. |
| Modelo de IA | Infraestructura por elegir | La API **no** infiere ni ejecuta modelos todavía. |

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
$env:MATICK_TOKEN="cambia-token-studio"
python -m matick_cloud.client direct chatgpt matick-chat matick-codex tarea.asignada '{"id":"demo-1"}'
python -m matick_cloud.client routes
```

`direct` solo acepta destinos explícitos, hasta siete por envío, y solo desde Matick Studio LM o ChatGPT. `routes` muestra las rutas autorizadas del token actual. Para ejecutar el ejemplo, genera tokens distintos para cada rol que esté activo; los tokens de ejemplo son **solo para desarrollo local** y no se deben utilizar tal cual en internet.

## Ejecutable Windows DirectX 12

Compila con **Windows SDK + Visual Studio 2022 C++ Build Tools + CMake**:

```powershell
cmake -S windows -B out/build -G "Visual Studio 17 2022" -A x64
cmake --build out/build --config Release
.\out\build\Release\MatickStudioLM.exe
```

El cliente utiliza `MATICK_CLOUD_URL` para consultar `/health`; por defecto comprueba `http://127.0.0.1:8787`. Para la nube utiliza una URL **HTTPS** real de tu despliegue. La revisión actual muestra un panel nativo Direct3D 12 y el estado de conexión: la mensajería privada desde el ejecutable todavía es una integración pendiente.

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
| API de eventos entre roles con matriz de rutas | **Implementada** (polling + SQLite) |
| Dirección de eventos de varios destinatarios explícitos | **Implementada** para Matick Studio LM y ChatGPT |
| Snapshot operativo hacia el rol `matick-pet` | **Implementado** en el bus; adaptador de mascota pendiente |
| Identidad por token distinto para cada rol | **Implementada** (MVP) |
| Windows `.exe` nativo DirectX 12 | **Código inicial**, verifica `/health`; panel de dirección pendiente |
| ChatGPT ↔ Matick Studio LM | Contrato y rutas preparados, **adaptador no conectado** |
| Alexa / Matick Reloj / Matick Codex / Matick Chat | Roles y rutas preparados, **adaptadores no conectados** |
| Ejecución de modelos IA en la nube | **No implementada** |
| Despliegue 24/7 y dominio | **No realizado** |

**Migración:** el proyecto anterior `IA-Local-Cursor / GemCo-Joystick` quedó preservado en la rama de respaldo `backup/ia-local-cursor-antes-matick-studio-lm-20261030`. Esta rama `main` comienza de cero, sin reaprovechar el MCP anterior.

Licencia: Apache-2.0 (se conserva el archivo LICENSE del repositorio).

