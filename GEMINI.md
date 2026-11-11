# GEMINI.md — Gemini CLI para Matick Studio LM / Matick Codex

Este archivo es la guía de contexto de **Gemini** en este repositorio. Morlet quiere incluir a «**Gemini Argon 4**» junto con GPT Codex y Claude Code para colaborar en su proyecto. **El nombre exacto del modelo, su disponibilidad, identificador técnico, cupo y costo deben comprobarse** en el entorno del usuario antes de seleccionarlo; este archivo no configura ni habilita ningún servicio.

## Lee antes de actuar

1. [Briefing maestro de Morlet](docs/BRIEFING_MAESTRO_MORLET_2026-11-11.md).
2. [Estado real / evidencia](docs/ESTADO_Y_EVIDENCIAS.md).
3. [Supervisor (NPU)](docs/SUPERVISOR_NPU.md).
4. [Autonomía y seguridad](docs/AUTONOMIA_SEGURIDAD.md).
5. [Matick Live Local](docs/MATICK_LIVE_LOCAL.md) cuando aplique.

## Comportamiento pedido

- Interpreta el briefing como **requisitos para implementar bajo orden concreta**, no como autorización para ejecutar o modificar por cuenta propia.
- Mantén la distinción entre Matick Studio LM, Matick Codex, Morlet Reloj, Manguito, LM Studio y laboratorio Pruebas.
- Implementa cambios mínimos, rastreables y reversibles. Compila y corre pruebas autorizadas, registra fallos y reintenta; si faltan pruebas, declara «sin verificar».
- **Nunca** marques algo como arreglado por opinión del modelo. No edites Windows, TPM, Defender, arranque, registro crítico o instalaciones.
- Para modelo premium, infraestructura externa, tareas destructivas, accesos y gastos: **pide autorización previa**. Un modelo no cambia automáticamente de otro proveedor a Gemini.
- Si colaboras con Codex/Claude: comparte diagnóstico, rutas, commits, pruebas y estados verificados, no secretos ni conversaciones privadas.

## Requisito especial de hardware

El supervisor es **Supervisor (NPU)**, exclusivo del Intel Core Ultra 5 225F. Todas sus pantallas y registros llevan sufijo **(NPU)**. Modelos, herramientas, RAGs, índices e historial se mantienen aislados de CPU/GPU; si no se verifica uso real de NPU, se informa y no se hace fallback silencioso.

**Al entregar:** especifica qué implementaste, evidencia de pruebas, qué quedó pendiente y cómo revertir cambios.
