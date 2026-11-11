# Matick Studio LM · Control de IA — instrucciones maestras

**Proyecto:** Matick Studio LM / Matick Codex (Windows). **Propietario:** Morlet. **Idioma:** español mexicano.

> **Estado al 11 de noviembre de 2026:** repositorio documental reactivado tras una limpieza deliberada. Aquí quedan las decisiones de nuestras conversaciones para **GPT/Codex, Claude Code y Gemini CLI**. No son prueba de que una función esté instalada, integrada o verificada en el PC.

## Empieza aquí

**[📘 Briefing maestro de Morlet](docs/BRIEFING_MAESTRO_MORLET_2026-11-11.md)**: visión, recursos, flujo autónomo, modelos, prioridades, restricciones y acuerdos del usuario.

Guías por agente: [`AGENTS.md`](AGENTS.md) (GPT/Codex), [`CLAUDE.md`](CLAUDE.md) (Claude Code) y [`GEMINI.md`](GEMINI.md) (Gemini CLI, incluido el nombre «Gemini Argon 4» referido por Morlet).

Especificaciones: [Supervisor (NPU)](docs/SUPERVISOR_NPU.md) · [Autonomía y seguridad](docs/AUTONOMIA_SEGURIDAD.md) · [Matick Live Local](docs/MATICK_LIVE_LOCAL.md) · [Estado y evidencias](docs/ESTADO_Y_EVIDENCIAS.md).

## Reglas clave

- **No mezclar proyectos:** Matick Studio LM y Matick Codex son distintos de Morlet Reloj, Manguito, LM Studio y otros repositorios.
- **Supervisor (NPU):** su modelo, herramientas, RAGs, índices, configuración y memoria son independientes. Etiqueta **`(NPU)`** siempre. No fallback silencioso a CPU, GPU o nube.
- **Autonomía con evidencia:** editar, compilar, probar, registrar errores, corregir y reintentar *dentro de un workspace autorizado*. Sin evidencia no se declara resuelto.
- **Seguridad:** no modificar Windows, Defender, TPM, arranque, archivos del sistema ni instalar software riesgoso. Cualquier elevación, operación destructiva o consumo premium requiere autorización explícita.
- **Costos:** modelo económico por defecto; modelos más caros solo cuando se justifiquen y Morlet apruebe el uso. No prometer cinco horas de créditos.
- **La documentación no es una orden automática:** los agentes solo ejecutan tareas cuando Morlet las solicita y dentro de los permisos disponibles.

## Ubicación del prototipo previo

El [PR #6 en `DannMorlet/Pruebas`](https://github.com/DannMorlet/Pruebas/pull/6) contiene **un prototipo de laboratorio** de memoria SQLite y configuración NPU, separado de este repositorio. No copiar ni activar ese código sin revisar cambios, seguridad, pruebas y autorización. El README de aquí no representa una app compilada.

## Flujo para continuar

1. Leer `README.md`, el briefing maestro y la guía del agente.
2. Identificar **qué es requisito, diseño, prototipo, prueba CI o verificación real**.
3. Seleccionar la tarea concreta solicitada; planear una implementación modular con respaldo y límites de permisos.
4. Probar y documentar resultados reproducibles; evitar PR o cambios masivos ajenos a la tarea.
