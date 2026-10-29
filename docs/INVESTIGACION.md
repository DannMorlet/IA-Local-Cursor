# Investigación aplicada: Manguito IA híbrida

Fecha: 2026-10-28. Hipótesis y prioridades basadas en la máquina del usuario, no en benchmarks propios. Fuentes oficiales al pie.

## Datos de hardware verificados y pendientes

- Intel Core Ultra 5 225F: 6P+4E, 10 núcleos, hasta 4.9 GHz, Intel AI Boost NPU con pico teórico de 13 TOPS INT8. Intel lo documenta; no confundir TOPS con tokens/s ni asumir que un modelo LLM corre en esa NPU.
- GPU del usuario: GeForce RTX 5060 con 8 GB VRAM. Priorizar modelos cuantizados pequeños y una sola tarea pesada de GPU por vez. No se promete que un modelo 8B quepa con cualquier contexto o cuantización.
- Memoria declarada: 2x16 GB DDR5-6000, total 32 GB. Ejecutar scripts/diagnostico-hardware.ps1 y revisar controladores.
- Windows 11 26H2: actualización anunciada como disponible por Microsoft en septiembre de 2026. El controlador Intel NPU consultado enumera sistemas hasta 25H2; confirmar compatibilidad práctica con 26H2 en la máquina antes de darlo por probado.
- Algunos modelos en OpenVINO y ciertas precisiones/operadores se ejecutan en NPU; otros usan CPU o GPU. Depende del gráfico y del controlador instalado.

## Selección sin suscripciones caras

| Trabajo | Primera opción | Alternativa / condicionante |
|---|---|---|
| Chat local | LM Studio ya instalado, /v1 | Ollama o llama.cpp como backend alterno |
| Agente de código | Aider (Git, diffs, terminal con revisión), modelos locales | Integrar Codex CLI / Claude Code únicamente si el usuario dispone de acceso válido; suscripciones/API con límites |
| Exploración Windows | Python pathlib + UI Automation/pywinauto + PowerShell | Win32 API y Playwright para apps web |
| Modelo CPU/NPU | OpenVINO y modelos específicos compatibles | CPU de respaldo; OpenVINO no garantiza todos los LLM |
| Imagen/video | ComfyUI por cola de workflows | Las GPUs de 8 GB necesitan diseños low-VRAM, paginación/tiling o inferencia lenta |
| Game streaming | Sunshine host + Moonlight Android | Steam Remote Play según juego |
| Acceso remoto | Tailscale/WireGuard y control de dispositivos | Solo red LAN para pruebas iniciales |
| Voz | Whisper.cpp o faster-whisper para STT y Piper/Kokoro para TTS tras evaluar | Cloud opcional con costos explícitos |
| GitHub | Ramas, PR, Actions para pruebas y empaquetado | No subir archivos de ~32 GB al repositorio normal |

## Estrategia específica de Manguito para una sola RTX

A. Modelo local pequeño genera plan, código o prompts. Guardar artefactos intermedios en disco.
B. Si un modelo optimizado y compatible existe en OpenVINO NPU, ejecutarlo allí. No equivale a trasladar una sesión en caliente desde llama.cpp/CUDA.
C. En cargas multimedia, descargar el LLM de GPU (LM Studio: descargar desde CLI/API disponible; Ollama: unload/stop). Verificar memoria con nvidia-smi.
D. Llamar API de ComfyUI /prompt con workflow previamente validado; recoger estados por WebSocket/historial; liberar VRAM cuando termine. Mantener una cola global con prioridades. **No** prometer dos modelos de difusión pesados simultáneos con 8 GB.
E. En modo juego, priorizar NVENC y game FPS. IA pesada se pausa o mueve a CPU/NPU si hay modelo compatible; nunca afirmar que la NPU acelera el motor gráfico de videojuegos.

## Sobre 'control total', ChatGPT Live y Claude

Se puede dotar al agente local de herramientas con lectura/escritura, terminal, automación GUI y pruebas, de alcance seleccionable. No se debe confundir una sesión de voz en la aplicación de ChatGPT con una API libre de cuota que controla el Windows ajeno en segundo plano. Integrar proveedores cloud requiere su API/CLI, autenticación y permisos según producto, y puede tener costo; el fallback abierto debe permanecer operativo sin ellos. GitHub Actions sirve para CI y compilación con runners disponibles, no es una GPU gratis ilimitada para ejecutar modelos pesados ni un acceso directo al escritorio.

## Galax​​y Fit3

Samsung documenta notificaciones y respuestas preestablecidas a mensajes, editables desde Galaxy Wearable. Investigar si la aplicación Android de Manguito puede emitir notificaciones con acción de respuesta que la Fit3 acepte; prototipo antes de prometer selección remota de cinco comandos. Si no admite RemoteInput para la app, se usa el móvil y se aprovecha el reloj para notificaciones.

## Seguridad y modo moto

No habrá control de escritorio mientras el usuario conduzca. Desde el parque o parado, uso normal por voz, con confirmaciones y redes privadas. Entrada por voz puede malinterpretarse: tareas de código siempre quedan registradas y cambios riesgosos requieren confirmación.

## Documentación y fuentes

- Intel 225F, NPU 13 TOPS: https://www.intel.com/content/www/us/en/products/sku/241069/intel-core-ultra-5-processor-225f-20m-cache-up-to-4-90-ghz/specifications.html
- Windows 26H2: https://learn.microsoft.com/en-us/windows/release-health/status-windows-11-26h2/
- Intel NPU driver: https://www.intel.com/content/www/us/en/download/794734/intel-npu-driver-windows.html
- OpenVINO requisitos: https://docs.openvino.ai/2026/about-openvino/release-notes-openvino/system-requirements.html
- OpenVINO NPU plugin: https://github.com/openvinotoolkit/openvino/blob/master/src/plugins/intel_npu/README.md
- LM Studio servidor: https://lmstudio.ai/docs/developer/core/server
- LM Studio herramientas: https://lmstudio.ai/docs/developer/openai-compat/tools
- Sunshine: https://docs.lizardbyte.dev/projects/sunshine/latest/
- Moonlight Android: https://f-droid.org/es/packages/com.limelight/
- ComfyUI rutas: https://github.com/Comfy-Org/docs/blob/main/development/comfyui-server/comms_routes.mdx
- ComfyUI MCP y coordinación de VRAM: https://github.com/Comfy-Org/comfy-mcp
- Aider: https://aider.chat/docs/
- Codex CLI: https://github.com/openai/codex
- Samsung Fit3: https://www.samsung.com/us/support/answer/ANS10004898/

## Próxima sesión

1. Desde Windows, ejecutar diagnóstico de hardware (sin permisos administrativos), confirmar NPU y prueba LM Studio /v1/models.
2. Probar la pasarela de esta rama con unittest; primero cambios en workspace de pruebas.
3. Instalar Sunshine/Moonlight, emparejar en la misma Wi-Fi, medir 1080p60 y latencia en estadísticas.
4. Implementar un cliente Android de controles y aprobaciones en un PR posterior.
5. Montar subagente de código con un modelo local que dé buen tool use y compararlo con 2-3 alternativas.
