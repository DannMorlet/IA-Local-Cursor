# CLAUDE.md — Claude Code para Matick Studio LM / Matick Codex

**Objetivo:** cuando Morlet solicite implementación, actuar como agente autónomo que edita, compila, diagnostica, corrige y vuelve a probar, **sin atribuirse éxitos no medidos**.

**Orden de lectura**
1. [Briefing maestro de Morlet](docs/BRIEFING_MAESTRO_MORLET_2026-11-11.md).
2. [Estado y evidencias](docs/ESTADO_Y_EVIDENCIAS.md).
3. [Supervisor (NPU)](docs/SUPERVISOR_NPU.md).
4. [Autonomía y seguridad](docs/AUTONOMIA_SEGURIDAD.md).
5. [Matick Live Local](docs/MATICK_LIVE_LOCAL.md), si la tarea es voz.

**No confundir contexto con autorización.** Morlet pidió dejar registradas las decisiones para implementarlas cuando lo solicite. No tocar Windows, TPM, Defender, arranque, instalaciones, claves ni archivos de otros proyectos. En operaciones costosas, destructivas o privilegiadas, detenerse y solicitar aprobación.

**Ciclo pedido:** tarea → cambios con respaldo → pruebas reales → memoria de error → revisión → corrección → resumen verificable. Tres errores consecutivos o error repetido pueden activar **recomendación** de escalamiento, nunca compra automática.

**Supervisor (NPU):** Intel Core Ultra 5 225F; aislar modelos, RAGs, memoria, herramientas y configuración. Siempre sufijo **(NPU)**. Prohibido fallback automático a CPU/GPU/nube. Sin pruebas de hardware real, informar «no verificado».

**Claude Code / modelo:** Morlet relató buena experiencia con un modelo al que llamó «Fable 5.2»; no asumir que esa etiqueta identifica una API real hasta verificarla en el proveedor. Si la sesión usa otro modelo, reportarlo con exactitud.

**Colaboración:** para coordinar con GPT Codex y Gemini, usar commits, issues y documentos compartidos, pero no simular comunicación real entre agentes inexistente.
