# Supervisor (NPU) — requisitos exclusivos de Matick Codex
**Estado:** propuesta aprobada en conversación para futura implementación; no hay benchmark ni inferencia real verificada en Intel 225F.

## Definición inequívoca

El usuario dijo: **«CPU o NPU dijiste. NPU»**. Por ello, el supervisor que se diseñe para clasificar errores y orientar a los demás agentes debe correr **en NPU**, no en CPU/GPU. Debe usar una instalación, almacenamiento y configuración dedicados, separados de los recursos de otros modelos/agentes.

La NPU del **Intel Core Ultra 5 225F** se describió como **13 TOPS INT8 nominales**. Eso **no** responde cuántos tokens por segundo genera. Benchmark obligatorio en la computadora real.

## Etiquetas siempre visibles

Cada interfaz, registro y aviso empleará sufijo literal:
- **Supervisor (NPU)**.
- **Modelo (NPU)**.
- **RAG (NPU)**.
- **Herramientas (NPU)**.
- **Memoria (NPU)**.
- **Historial (NPU)**.
- **Estado (NPU)**.
- **Configuración (NPU)**.

Se puede usar una sección de «recursos/racks (NPU)» para organizar funciones, pero **«racks»** se recogió de voz y puede referirse a **RAGs**. No renombrar datos del usuario ni interpretar una migración sin confirmar semántica.

## Áreas independientes sugeridas

```text
npu/
  modelos/
  herramientas/
  rag/
    documentos/
    embeddings/
    indices/
  memorias/
  historial/
  configuracion/
  pruebas/
```

Ruta final decidida según instalación real, siempre dentro de un directorio autorizado; **no** modificar Windows ni compartir índices y memorias de otras aplicaciones por defecto.

## Políticas técnicas

1. **NPU obligatoria**, sin fallback automático a CPU, GPU, `AUTO`, `MULTI` o nube. Si no se puede ejecutar realmente en NPU, mostrar `Supervisor (NPU): no disponible` y solicitar decisión del usuario antes de buscar otra vía.
2. Probar **runtime** y operadores en **NPU física**. Un backend que dice NPU puede tener operaciones en CPU; medir y declarar distribución real.
3. El supervisor recibe eventos mínimos como `issue_id`, error, prueba, proyecto y prioridad; evita copiar chats completos, secretos o repositorios.
4. El supervisor **propone**, pero un programa de pruebas independiente verifica. Las reglas de protección de Windows y gasto premium no quedan a discreción exclusiva del modelo.
5. Las herramientas y RAGs (NPU) requieren permisos específicos y capacidad de cancelación. Mantener registro de auditoría.
6. Sin actualizaciones automáticas de drivers, Python global, TensorRT, OpenVINO u otros runtimes. Si una versión requiere Python distinto, crear entorno de proyecto dedicado.

## Modelos a evaluar, sin declarar instalación

- **Qwen3-1.7B INT8:** prioridad inicial por balance de tamaño/capacidad.
- **Qwen3-4B INT8:** alternativa de mayor capacidad con posible incremento de latencia.
- **Otros modelos contemporáneos y motores alternativos a OpenVINO:** investigarlos por compatibilidad efectiva con NPU de 225F y licencias, no por nombre o marketing.

Las versiones y el funcionamiento real en NPU **no están verificados** para la PC de Morlet. Objetivo: detectar fallos y decidir rutas sin limitarse a respuestas tan superficiales como las que Morlet percibió con Qwen 2.5.

## Benchmark y aceptación

Medir tokens/s **prefill y generación**, tiempo al primer token, latencia por decisión, consumo RAM/VRAM, funcionamiento con diferentes longitudes de error, tasa de decisiones correctas, porcentaje de fallbacks observados y estabilidad. Publicar scripts de medición y resultados reproducibles.

**Aceptación:** NPU identificada y usada; registros que lo prueben; herramientas y RAGs segregados; interfaz etiqueta `(NPU)`; fallos seguros sin fallback; autonomía y costos restringidos. **No declarar cumplido solo por CI de código.**

Consultar [briefing maestro](BRIEFING_MAESTRO_MORLET_2026-11-11.md) y [estado](ESTADO_Y_EVIDENCIAS.md).
