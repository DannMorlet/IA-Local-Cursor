# Estado y evidencias — Matick Studio LM / Matick Codex
**Fecha del registro:** 2026-11-11  
**Regla:** este registro diferencia conversación, documentación, prototipos y comprobaciones reales. Actualizarlo después de cada intervención con evidencia, no declaraciones vagas.

| Componente | Estado conocido | Evidencia / límite |
| --- | --- | --- |
| Guías para GPT Codex, Claude y Gemini | **Documentado en este repositorio** | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` y briefing maestro en `main`. |
| Supervisor (NPU), nombres y recursos aislados | **Especificado, no integrado** | `docs/SUPERVISOR_NPU.md`; no hay datos de inferencia real en Intel 225F. |
| Modelo Qwen3-1.7B INT8 en NPU | **Candidato, no verificado** | Sin benchmark de tokens/s ni confirmación de backend efectivo. |
| Modelo Qwen3-4B INT8 en NPU | **Alternativa, no verificada** | No hay latencia medida ni pruebas de operaciones/fallback. |
| Autonomía de reparación Matick Codex | **Requisito; prototipo experimental en otro repo** | Laboratorio `Pruebas` [PR #6](https://github.com/DannMorlet/Pruebas/pull/6). Ninguna conexión a este repositorio está implicada. |
| Memoria SQLite + pruebas mínimas | **Código experimental de laboratorio** | El PR #6 contiene implementación inicial. Comprobar estado del CI para el **commit concreto** antes de afirmar verde; no hay sandbox real para tests no confiables. |
| Seguridad Windows, TPM, Defender, no malware | **Política documentada, no certificación de aislamiento** | Faltan pruebas de sandbox y revisión de seguridad de un ejecutor real. |
| Selección Sol/Astra/alternativas con costos | **Política documentada** | No hay selector conectado a una API de pago ni autorización automática. |
| Gemini CLI y «Gemini Argon 4» | **Guía documental `GEMINI.md`** | No hay modelo descargado/configurado por este cambio; revisar denominación, acceso y cuotas vigentes. |
| Matick Live Local: ASR/LLM/TTS | **Diseño; no funciona aún como voz real** | No existe prueba en bocinas o micrófono de esta implementación; el PC no cuenta con micrófono según Morlet. |
| Python 3.15 | **Versión discutida / CI de laboratorio** | El propio runtime NPU puede requerir Python separado; no instalado ni verificado aquí. |
| Interfaz Windows Matick Studio LM | **Requisitos recuperados** | `main` contiene documentación, no un EXE funcional ni pruebas GUI. |

## Lo que sí se confirmó en esta intervención

- La rama `main` de `DannMorlet/IA-Local-Cursor` se encontraba vacía al consultar GitHub al inicio.
- Morlet **autorizó empezar a llenarla ahora** con lo conversado.
- Se comenzaron a crear archivos de instrucciones y documentación **directamente en `main`** para que herramientas futuras lean el contexto del producto correcto.
- El laboratorio `DannMorlet/Pruebas` y su PR #6 permanecen separados.
- **No se corrió software en Windows, no se instalaron pesos de modelos, no se activaron servicios premium, no se cambió TPM ni Defender.**

## Próxima intervención técnica — solo bajo petición de Morlet

1. Auditar librerías y repositorios reales, elegir un módulo acotado para la primera implementación.
2. Hacer prototipo **Supervisor (NPU)** con modelo/runtimes de NPU confirmados; registrar dónde se ejecutan realmente los operadores.
3. Medir benchmarks de NPU con prompts y errores representativos; no inferir tokens/s por TOPS.
4. Hacer ejecutor de pruebas con aislamiento para Matick Codex, historial persistente, autorización premium, rollback y logs.
5. Integrar interfaz Windows y pruebas en dispositivo; reporte verificado.
6. Cuando exista micrófono, avanzar con Matick Live Local por fases y medir latencia/interrupciones.

## Cómo registrar futuras verificaciones

Para cada cambio: fecha, nombre de rama/commit, ruta, entorno real, comando, salida resumida, pruebas exitosas/fallidas, evidencia asociada, bloqueos y cómo revertirlo. Si se ejecuta solo en CI, **no** escribir «probado en la PC de Morlet». Si una prueba no se realizó, declararlo.

[Inicio](../README.md) · [Briefing maestro](BRIEFING_MAESTRO_MORLET_2026-11-11.md) · [Supervisor (NPU)](SUPERVISOR_NPU.md)
