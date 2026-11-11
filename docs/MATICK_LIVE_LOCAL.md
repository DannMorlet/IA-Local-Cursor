# Matick Live Local — voz completamente local para Matick Studio LM
**Estado:** idea y requisitos de Morlet, sin implementación de voz verificada.

## Objetivo

Conversar de manera natural en PC Windows sin internet, con respuestas habladas y posibilidad de interrumpir. Inspiración de experiencia: GPT Live; **no** presupone acceso a pesos GPT Live ni equivalencia de capacidades/latencia.

## Condiciones reales

- Equipo: RTX 5060 con **8 GB VRAM**, 32 GB RAM, CPU Core Ultra 5 225F, NPU nominal 13 TOPS INT8. Morlet acepta almacenar hasta 500 GB de modelos en disco, **sin exigir mantenerlos todos residentes**.
- **No tiene micrófono en la PC por ahora**, según última conversación, y Matick Studio LM aún no tiene voz funcional. No pedir compra costosa ni anunciar pruebas de entrada de voz.
- UI principal de chat texto siempre funcional. Voz debe ser **módulo opcional**, desactivado por defecto cuando no esté habilitado.

## Arquitectura modular candidata

1. Voz→texto: evaluar **Qwen3-ASR** offline y alternativa apropiada de español mexicano.
2. Procesamiento conversacional: evaluar **Qwen3.5-4B** cuantizado u otro compatible con rendimiento real aceptable.
3. Texto→voz: evaluar **Piper es-MX**, comparando naturalidad y latencia; **Qwen3-TTS** como investigación, no requisito inicial.
4. Detector de habla: p. ej. **Silero VAD**; cancelación de eco y detección de interrupción/turn-taking.
5. Trazas: medir latencias por etapa, uso de GPU/CPU, consumo, audio cortado, interrupciones y calidad del texto/voz.

Estos nombres fueron propuestas verbales, no dependencias ni modelos instalados. Verificar licencias, versiones, configuraciones y compatibilidad.

## Plan incremental para futura orden de implementación

- **Fase 0:** interfaz en texto y API de modelo local comprobadas.
- **Fase 1:** texto→voz probado en bocinas **sin micrófono**, usando texto escrito.
- **Fase 2:** al conectar micrófono, voz→texto con pruebas de privacidad y sin internet.
- **Fase 3:** streaming parcial, cancelación de habla y barge-in sin eco, medición en dispositivo.
- **Fase 4:** mejor tono/voz natural, preferencia es-MX, y posible alternancia teatral «Morlet/GPT» si el motor de voz permite voces separadas.

Morlet expresó preferencia por **pausas entre turnos** de «Morlet» (voz masculina natural) y «GPT» (voz femenina natural), pero no entre cada palabra, y sin exagerar ternura/bostezos. Evitar prometer control real de voz donde no existe. 

**No confundir** el motor del supervisor **(NPU)** con el motor conversacional de Live Local. Mantener configuraciones y recursos independientes.

Leer [briefing maestro](BRIEFING_MAESTRO_MORLET_2026-11-11.md) y [estado y evidencias](ESTADO_Y_EVIDENCIAS.md).
