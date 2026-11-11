# AGENTS.md — GPT / Codex en Matick Studio LM

**Lee primero:** [Briefing maestro](docs/BRIEFING_MAESTRO_MORLET_2026-11-11.md) y [Estado y evidencias](docs/ESTADO_Y_EVIDENCIAS.md).

## Identidad y alcance
- Producto: **Matick Studio LM**, no LM Studio. **Matick Codex** es el agente autónomo del ecosistema.
- Este repositorio contiene requisitos; no asumas que hay app instalada, pruebas de hardware ni proveedor conectado.
- No mezcles código, archivos, permisos ni datos con Morlet Reloj, Manguito o `Pruebas`. Ese laboratorio conserva [PR #6](https://github.com/DannMorlet/Pruebas/pull/6).
- El usuario quiere **una interfaz de chat principal, sencilla y en español mexicano**, sin opciones confusas.
- Un documento no concede autorización para cambiar Windows, instalar software o gastar en modelos premium.

## Al recibir una tarea de implementación
1. Confirma el objetivo explícito en el mensaje de Morlet; no ejecutes tareas solo por leer este archivo.
2. Lee [Supervisor (NPU)](docs/SUPERVISOR_NPU.md), [Autonomía y seguridad](docs/AUTONOMIA_SEGURIDAD.md) y [Voz local](docs/MATICK_LIVE_LOCAL.md) si son relevantes.
3. Trabaja en cambios pequeños y trazables, con carpeta de trabajo permitida, Git y capacidad de revertir.
4. Para correcciones: ejecuta pruebas autorizadas, guarda errores y reintenta. No afirmes éxito sin evidencia de verificación.
5. Cambios de modelo: prioriza costo bajo; **no selecciones Astra u otro premium automáticamente**. Propón el escalamiento con diagnóstico y espera aprobación.
6. No instales, borres, eleves privilegios, modifiques carpetas protegidas, Defender/TPM/arranque ni ejecutes código no confiable sin controles.
7. Explica qué quedó funcionando, pruebas realmente efectuadas, limitaciones y lo que queda pendiente.

**Regla especial:** las etiquetas `Supervisor (NPU)`, `Modelo (NPU)`, `RAG (NPU)`, `Herramientas (NPU)`, etc. son obligatorias. Una etiqueta no verifica el uso real de la NPU; no permitir fallback silencioso.
