# Estado y evidencias — Matick Studio LM / Matick Codex
**Fecha del registro:** 2026-11-11 (actualizado por Claude Code tras trabajar en la PC de Morlet)
**Regla:** este registro diferencia conversación, documentación, prototipos y comprobaciones reales. Actualizarlo después de cada intervención con evidencia, no declaraciones vagas.

Niveles usados: **verificado en la PC** (se ejecutó en Matick Studio LM en marcha), **probado en aislamiento** (el módulo se ejecutó solo, fuera de la app), **sin hacer**.

## Ya sirve — verificado en la PC de Morlet (2026-11-11)

Entorno de las pruebas: Matick Studio LM en Windows 11, motor llama.cpp local, modelo Matick Gemma E2B con contexto 16384 en la RTX 5060, interfaz real manejada desde un navegador contra el servidor local. Sin créditos ni servicios de pago.

| Función | Evidencia | Límite |
| --- | --- | --- |
| Opciones del modelo como botones de un clic en el chat | Una conversación guardada con «Opciones: A \| B \| C» y su lista debajo mostró tres botones; el clic envía la opción | El globo de la mascota recibe las mismas opciones, pero no se vio en la ventana nativa |
| Barra de botones del cuadro de escribir que se acomoda sola | Vista con sus botones reales en la interfaz | — |
| Memoria de conversación | Antes solo se enviaban 12 mensajes al modelo. Ahora hasta 400, con archivo permanente por conversación y recuerdo automático por turno. Con 46 mensajes recordó un código y un nombre dichos en el mensaje 1, con chat guardado y sin guardar | Recuperación por palabras, no un contexto de un millón; sin probar con modelos de 9B/35B ni tras compactar |
| Velocidad con historial largo | Recuerdos y RAG van al final del prompt para reutilizar la caché de llama.cpp. De 2.8–4.9 s por turno a 1.4–2.8 s en la mayoría de los turnos, con más tokens de entrada | Dos turnos tardaron 4.6–4.8 s; generación 126–157 tokens/s frente a 158 |
| Equipo de agentes visible en «En vivo» | Una delegación real mostró al agente principal y al subagente con su estado y su tarea | Solo con un subagente |
| Honestidad en la delegación | Encontrado y corregido: el subagente devolvía una llamada en crudo y el principal inventaba el informe; un especialista ya no se delega a sí mismo | Tras el arreglo no se logró repetir una delegación real; la nota de «no se consultó a ningún subagente» no se vio dispararse |

## Probado en aislamiento — falta verlo dentro de la app

| Función | Evidencia | Límite |
| --- | --- | --- |
| Memoria de errores (briefing, sección F) | Módulo de incidencias: agrupa fallos e intentos, huella de error estable, entorno y fecha; solo marca resuelto con código de salida 0 del ejecutor; recuerda soluciones confirmadas dentro del mismo proyecto; dos errores iguales o tres fallos seguidos recomiendan diagnóstico | Ejecutado con datos de prueba; sin una tarea real de Matick Code |
| Búsqueda en la memoria de conversación a gran escala | 1.8 ms sobre 1,202 mensajes | Datos sintéticos |

## Reportado por GPT en sesiones anteriores — no comprobado de nuevo en esta intervención

| Componente | Lo que se reportó | Límite |
| --- | --- | --- |
| Supervisor (NPU) | Clasificador de incidencias con OpenVINO ejecutado en Intel AI Boost; consulta «Estado del Supervisor NPU» | Sin benchmark de tokens/s; falta registrar el dispositivo real en cada inferencia |
| Qwen3-1.7B INT8 en NPU | Carga y generación desde el motor de Matick; botón «NPU» | Sin prueba visual del botón ni medición de velocidad |
| Agente de programación local | Corrigió un archivo JavaScript y pasó cuatro pruebas independientes | Un solo caso; sin medición en proyectos de varios archivos |

## Aún no sirve / sin hacer

- **Ejecutor de pruebas con aislamiento real.** Matick Code valida rutas; eso no es un sandbox.
- **Subagentes autónomos.** Un subagente es una sola consulta al modelo, por turnos: no usa herramientas por su cuenta ni trabaja a la vez que otros.
- **Contexto de un millón de tokens.** No existe; lo que hay es recuperación de recuerdos.
- **Trabajo unido a «En vivo» dentro del chat**, con la mascota que muestra, resume, pregunta con botones y aprende de las respuestas. Pedido por Morlet el 2026-11-11; pendiente para GPT.
- **Selector de modelo con costo y aprobación.** Sin hacer.
- **Matick Live Local (voz).** Sin hacer; la PC no tiene micrófono.
- **Jugador de videojuegos en partida real** (Sudeki): sin tasa de éxito medida.
- **Iniciador que recupere la ventana abierta** en lugar de fallar al abrir Matick dos veces.
- **Equivalencia con modelos de pago en proyectos largos.** No hay evidencia.

## Qué no se tocó

No se modificó Windows, Defender, TPM ni el arranque. No se instaló software ni se usaron servicios de pago. Los cambios quedaron dentro de la carpeta de Matick Studio LM, con respaldo de los archivos editados salvo dos módulos, anotados en el registro local de cambios.

## Cómo registrar futuras verificaciones

Para cada cambio: fecha, ruta, entorno real, comando, salida resumida, pruebas exitosas/fallidas, bloqueos y cómo revertirlo. Si se ejecuta solo en aislamiento o en CI, **no** escribir «probado en la PC de Morlet». Si una prueba no se realizó, declararlo.

[Inicio](../README.md) · [Briefing maestro](BRIEFING_MAESTRO_MORLET_2026-11-11.md) · [Supervisor (NPU)](SUPERVISOR_NPU.md)
