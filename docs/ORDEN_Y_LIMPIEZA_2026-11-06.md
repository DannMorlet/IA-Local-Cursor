# Orden y limpieza de Matick Studio LM — auditoría 2026-11-06

> **Solo índice de mantenimiento, sin tocar el motor de inferencia, Windows, instaladores o historia Git.** Se aplicaron etiquetas de GitHub a PR abiertos. `main` sigue siendo la base estable de Matick Studio LM Cloud, independiente de **LM Studio** y **Manguito**.

## Ruta de trabajo prioritaria

1. [PR #58](https://github.com/DannMorlet/IA-Local-Cursor/pull/58) — Matick Cloud v1.2 con inferencia GGUF vía llama.cpp; PR de base, todavía borrador.
2. [PR #59](https://github.com/DannMorlet/IA-Local-Cursor/pull/59) — paquete Windows, **basado en rama de #58**; revisar antes de integrarlo.
3. [PR #63](https://github.com/DannMorlet/IA-Local-Cursor/pull/63) — validación de URL heredada, **basado en #59**.
4. [PR #65](https://github.com/DannMorlet/IA-Local-Cursor/pull/65) — prueba de entorno/rollback, **basado en #63**.
5. [PR #60](https://github.com/DannMorlet/IA-Local-Cursor/pull/60) → [#61](https://github.com/DannMorlet/IA-Local-Cursor/pull/61) → [#62](https://github.com/DannMorlet/IA-Local-Cursor/pull/62) — cadena independiente de robustez del inventario GGUF. Bases consecutivas: #60 sobre #58, #61 sobre #60, #62 sobre #61.

**Precaución:** #58, #59, #60 no son solicitudes intercambiables. La rama [#64](https://github.com/DannMorlet/IA-Local-Cursor/pull/64) también implementa inferencia GGUF desde `main`, y puede solaparse con #58: comparar arquitecturas y tests antes de decidir. No fusionar ambas a ciegas.

## Trabajo paralelo por área

| Área | PR | Qué revisar |
|---|---|---|
| Seguridad y calidad de Cloud | [#66](https://github.com/DannMorlet/IA-Local-Cursor/pull/66), [#54](https://github.com/DannMorlet/IA-Local-Cursor/pull/54), [#53](https://github.com/DannMorlet/IA-Local-Cursor/pull/53) | Salud/assets sin secretos, CI completa, identidad real del modelo |
| Estado de tareas y chat | [#52](https://github.com/DannMorlet/IA-Local-Cursor/pull/52), [#50](https://github.com/DannMorlet/IA-Local-Cursor/pull/50), [#49](https://github.com/DannMorlet/IA-Local-Cursor/pull/49) | Persistencia, marcas de tiempo, avisos de truncamiento |
| Windows/DPI/portable | [#56](https://github.com/DannMorlet/IA-Local-Cursor/pull/56), [#47](https://github.com/DannMorlet/IA-Local-Cursor/pull/47) | Arranque con carpeta correcta, DPI, smoke real Windows |
| Integración MCP/agentes | [#18](https://github.com/DannMorlet/IA-Local-Cursor/pull/18), [#8](https://github.com/DannMorlet/IA-Local-Cursor/pull/8) | Independencia del núcleo y ausencia de secretos |
| Plan de entrenamiento | [#35](https://github.com/DannMorlet/IA-Local-Cursor/pull/35) | Es planificación, no un motor de entrenamiento implementado |
| Fuera de categoría | [#1](https://github.com/DannMorlet/IA-Local-Cursor/pull/1) | «Manguito Studio v0.2» está en el repo de Matick Studio LM: estudiar migración documental a Manguito **sin perder la rama** |

## Criterios de integración y limpieza futura
- Confirmar pruebas Python/Windows, firma y reversión antes de fusionar.
- Para cadenas apiladas, revisar dependencias de `base` y aplicar un orden explícito; no contar cada PR como una función independiente.
- Distinguir funciones **ya presentes en main** de previews. Probar en `C:\IA\Matick Studio LM` antes de sustituir ejecutables locales.
- Mover o cerrar una propuesta solo tras verificar su equivalente en una rama integrada; conservar historial y discusiones.
- No eliminar ramas ni artefactos de instalación automática durante esta fase.
- **Seguridad:** `main` no tenía protección GitHub activa al momento de consultar. Configurar reglas de rama y revisiones desde Settings cuando el propietario lo autorice.

[Mapa de los cuatro repositorios](https://github.com/DannMorlet/Pruebas/blob/main/docs/MAPA_REPOSITORIOS_MORLET.md).
