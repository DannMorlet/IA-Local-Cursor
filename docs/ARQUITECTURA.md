# Arquitectura Manguito — local primero, nube como respaldo

Estado: diseño v0.1 (28 de octubre de 2026), implementación incremental. El presente repositorio aún no representa el asistente final.

## Dos planos independientes

1. **Plano de automatización**. El agente Manguito recibe objetivos y trabaja en directorios autorizados. Usa herramientas de exploración, edición, planificación, pruebas y control de interfaces únicamente cuando se instalen y autoricen. Una política exige consentimiento antes de borrar, instalar, ejecutar comandos desconocidos, cambiar ajustes críticos o subir datos.
2. **Plano de streaming**. Sunshine codifica el escritorio/juego por hardware en el host Windows; Moonlight presenta el stream y transporta teclado, ratón, touch y gamepad de vuelta desde Android. La IA no pasa por cada fotograma, para evitar añadir latencia. Acceso a distancia con red privada autenticada, sin abrir puertos a Internet cuando sea viable.

Flujo objetivo:

    Teléfono Android ─── Moonlight (táctil, juego, pantalla) ── Sunshine ── Windows
             │
             └── voz, estado, tareas, aprobaciones ─── túnel privado autenticado ── Manguito Gateway
                                                                           │
                  ┌────────────── modelo local LM Studio (texto/código) ───┤
                  ├────────────── NPU OpenVINO (modelos compatibles) ─────┤
                  ├────────────── GPU ComfyUI (imagen/video) ─────────────┤
                  ├────────────── herramientas de Windows/VS Code ───────┤
                  └────────────── GitHub PR + API opcional Claude/OpenAI ─┘

La Galaxy Fit3 NO es un equipo Wear OS genérico. Su integración prevista es notificación y respuesta rápida 1–5 vía aplicación complementaria Android, sujeta a lo que permita Samsung y el tipo de notificación. No se promete ejecución de una APK nativa en la pulsera.

## Coordinador de recursos GPU / NPU / CPU

- RTX 5060 8 GB: principal para visión pesada, modelos locales que quepan, codificación NVENC y generación de imagen/video; al jugar, priorizar juego y streaming, y descargar modelos de GPU.
- Core Ultra 5 225F: Intel AI Boost NPU 13 TOPS teóricos INT8, más inferencia de CPU. Verificar controlador y detección real con OpenVINO antes de asignar modelos al NPU.
- RAM 32 GB: permite almacenamiento temporal, modelos cuantizados con descarga parcial a CPU, pero el rendimiento depende de ancho de banda y carga.
- Un modelo de LM Studio en GPU no se migra en caliente al NPU por arte de magia. Para 'enrutamiento' ejecutar modelos compatibles distintos en sus runtimes, liberar memoria de LM Studio y lanzar workflows ComfyUI después. El agente observa uso real y arbitra reservas/colas.
- ComfyUI: API de cola para imagen/video y endpoint de descarga/liberación de memoria; los workflows y pesos se alojan en el PC (no en Git).

## Control completo progresivo

**Nivel 0 ya implementado**: modelos por API compatible, enumerar y leer archivos de texto solo en workspace, propuesta diff, aprobación de escritura por el propio PC; puerto 127.0.0.1:8765. Sin ejecución de terminal.

**Nivel 1**: telemetría de procesos, ventanas y monitores; inventario de archivos con exclusiones por glob; capturas bajo demanda (Windows Graphics Capture, DXGI o mss); APIs UI Automation/pywinauto; OCR + visión local. Captura/grabación con indicador visible y consentimiento. OBS/FFmpeg para grabar solo sesiones elegidas.

**Nivel 2**: herramientas con contratos estrictos: abrir programa permitido, ejecutar pruebas dentro de worktrees, Git diff/commit/rollback, editar VS Code, operar mouse/teclado por ventanas, automatización Playwright para navegador. Registro de cada acción, dry-run, timeout, botón STOP. Prohibir ejecución persistente como administrador y ejecución arbitraria desde web sin validación.

**Nivel 3**: agente planificador y subagentes (código, pruebas, documentación, imágenes). Enrutamiento por privacidad, VRAM disponible, longitud y complejidad: modelo local primero; cuando se autoriza, derivar consulta acotada a Claude o OpenAI API. Las suscripciones a ChatGPT/Claude y sus APIs no se consideran bolsas intercambiables. Si falla el acceso o hay límite: cola para recuperación local o generar PR en GitHub sin 'inventar' ejecución de la nube.

**Nivel 4**: Android de cuatro acciones con menú: Hablar / Ver PC / Tareas / Emergencia-Parar; pantalla táctil de baja latencia gestionada por Moonlight, no por un flujo de capturas de IA. Autenticación del dispositivo, revocación y aprobación de cambios riesgosos por notificación interactiva. Galaxy Fit3 respuestas rápidas solo tras probar la compatibilidad.

**Nivel 5**: afinación, distilación, entrenamientos y pipeline texto -> prompt visual -> NPU compatible -> descarga de modelos LLM en GPU -> ComfyUI en GPU -> imagen o video. Medir tokens/s, TTFT, VRAM, FPS, latencia P50/P95, uso de NPU y costo real por tarea.

## Reglas no negociables

1. Exponer el Gateway directamente en la LAN/Internet no es parte del MVP; mantener localhost. Para redes móviles usar emparejamiento y red privada (Tailscale/WireGuard) con autenticación de aplicación y permisos separados.
2. Nunca subir pesos, datos privados, tokens, grabaciones o proyectos personales a GitHub sin selección explícita; usar .gitignore y secretos aislados.
3. Antes de cambios masivos, crear rama y copia de seguridad. Todas las acciones son auditables y reversibles cuando sea posible.
4. La autorización remota de operaciones destructivas debe ser explícita, con plazo, identidad y alcance. Sin modo 'sin límites' frente a daños accidentales.
5. Conduciendo motocicleta: no usar pantalla, controles remotos ni órdenes de trabajo que distraigan. Solo avisos pasivos no urgentes si son apropiados; retomar tareas al detenerse.

## Criterios de aceptación

- 100% pruebas en CI sobre código de esta rama.
- Leer y proponer un cambio dentro del workspace: correcto; acceso a ../, .git y .env: bloqueado.
- Un cambio no se ejecuta si la política de escrituras está apagada, falta el código o cambió el archivo.
- LM Studio responde solo si el modelo realmente está cargado; sin respuestas simuladas.
- Streaming de juego a 1080p/60 inicialmente, medido con estadísticas de Moonlight; escalar a 90/120 FPS si red, host y pantalla lo permiten. No prometer latencia absoluta a través de 4G/5G.
- NPU detectada por sistema, driver y OpenVINO antes de declarar compatibilidad de un modelo.
