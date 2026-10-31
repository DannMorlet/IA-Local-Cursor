# Matick Studio LM — LM Studio JS, ramas experimentales y MCP

## Decisión arquitectónica

**Matick Studio LM es una plataforma distinta de LM Studio.** Usamos el SDK oficial **`@lmstudio/sdk` v2.1.0** como biblioteca y *proveedor opcional* de modelos, no como el motor obligatorio. La nube Python y la ventana nativa C++ / DirectX 12 no dependen de instalar LM Studio. La capa Node `integrations/toolhub` sirve de adaptador autónomo a modelos y MCP.

Biblioteca analizada: https://github.com/lmstudio-ai/lmstudio-js . El árbol `main` comprobado en esta investigación apuntaba a `4b9af903e866808013524eece1e9ceb7a7f18c68` (30–31 octubre 2026), `publish/sdk/package.json` declaraba versión **2.1.0** y licencia **MIT**. Se declara una dependencia npm; **no copiamos su código ni incorporamos automáticamente código de ramas experimentales**.

## Ramas consultadas

La página https://github.com/lmstudio-ai/lmstudio-js/branches muestra más de 100 ramas; `main` era protegida al consultarla. Las ramas `alex/*`, `matt/*`, `neil/*`, `rugved/*`, `ryan/*` parecen ramas de trabajo y no deben confundirse con publicaciones estables.

| Tema de interés para Matick | Rama de investigación | Decisión |
| --- | --- | --- |
| Decodificación especulativa | `alex/speculative-decoding-changes` | Investigar API publicada y benchmarks antes de adaptar |
| Offload de GPU | `matt/n_gpu_layers_auto` | Investigar configuración sin presuponer soporte NPU |
| OpenVINO | `neil/openvino-settings` | Evaluación experimental; no activado |
| Eventos de herramientas | `matt/recieve-new-tools-events` | Investigar compatibilidad MCP |
| Sondeo de hardware | `rugved/hardware-survey` | No recopilar telemetría sin consentimiento |
| Autenticación | `ryan/adds-auth` | Inspiración; no usar credenciales ni código experimental |

**Política:** investigar ramas como material técnico, comparar con `main`, y usar versiones npm publicadas por defecto. Cambiar de versión solo después de pruebas CI, revisión de seguridad/licencias y una bandera experimental. No hay sincronización automática ni compilación de todos los forks.

## Cómo usar `@lmstudio/sdk` como proveedor opcional

En una PC con Node 20+ y una instancia compatible de LM Studio iniciada:

```powershell
cd integrations/toolhub
npm install
$env:MATICK_LMSTUDIO_WS = "ws://127.0.0.1:1234"
node src/cli.mjs models
node src/cli.mjs chat "Hola desde Matick Studio LM"
```

El SDK utiliza **WebSocket `ws://`/`wss://`**, no la URL HTTP `/v1` de las API estilo OpenAI. Para una instancia remota el adaptador requiere `wss://`. El puerto y compatibilidad dependen de la instancia activa.

El modelo puede no estar cargado. En ese caso debe informarse el error real; el adaptador no lanza otro motor ni inventa respuestas.

## MCP y `mcp.json`

En la rama histórica del repositorio Matick se encontró un `mcp.json` que declaraba **ocho** servicios: `cursor`, `matick-echo`, `velocidad`, `refuerzo`, `agente-enrutador`, `mascota.mcp`, `chat_server.mcp` y `gemco-joystick`. Los servidores originales apuntaban a scripts de un PC anterior y no se despliegan en la nube.

Copiar `mcp.example.json` como `mcp.json`, corregir las rutas **solo en tu PC**, y habilitar explícitamente los servicios que efectivamente estén instalados. Nunca subir secretos ni rutas personales al repositorio.

```powershell
cd integrations/toolhub
Copy-Item mcp.example.json mcp.json
node src/cli.mjs mcp:list
# Solo tras revisar las rutas, permisos y activar enabled=true:
$env:MATICK_MCP_EXEC_ENABLED = "1"
node src/cli.mjs mcp:tools gemco-joystick

# El uso real de herramientas exige además:
$env:MATICK_MCP_ACT_ENABLED = "1"
node src/cli.mjs mcp:call gemco-joystick gemco_status "{}"
```

El cliente MCP solo admite servidores locales **stdio** usando Python o Node, no ejecuta shell, y las llamadas deben figurar en `allowedTools`. La lista de herramientas sirve para comprobar capacidades y no garantiza que controladores, modelos o dispositivos existan. **Nunca activar control del PC ni captura por defecto.** El propio GemCo Joystick puede exigir un segundo panel local para ARMAR y disponer de parada de emergencia, independientemente del permiso del ToolHub.

El SDK de LM Studio no sustituye al cliente MCP; ambos quedan bajo el ToolHub de Matick. Los resultados MCP son datos no confiables y no justifican ejecución automática de comandos.

## Estado técnico

- Proveedor `lmstudio-js`: implementado como adaptador JS opcional; requiere instalación de dependencias y servidor LM Studio activo para una prueba real.
- MCP: registro, cliente JSON-RPC stdio y allowlist con opt-in; se puede probar con servidor simulado.
- Configuración original de ocho servidores: catalogada, **no activada**. Se requieren scripts locales reales.
- Conexión ToolHub ↔ nube Matick: pendiente de un puente autenticado por cuenta.
- Conexión UI DirectX 12 ↔ ToolHub: pendiente. El ejecutable no carga Node de manera oculta.
- ChatGPT, Alexa, reloj, mascota MCP: no integrados aún mediante esos adaptadores.

## Seguridad / licencias

El proyecto Matick conserva Apache-2.0. `@lmstudio/sdk` se instala separadamente por npm bajo MIT, según `publish/sdk/package.json`. No se hacen copias de ramas ni se redistribuyen binarios de LM Studio. No poner `mcp.json` con rutas/secretos reales en Git. En producción usar autenticación delegada, TLS para acceso externo, límites y registros mínimos.

El ToolHub es inicial: los servidores MCP locales pueden ejecutar el código indicado por el usuario en su configuración. Revisa su procedencia antes de habilitarlos; no es un sandbox completo.
