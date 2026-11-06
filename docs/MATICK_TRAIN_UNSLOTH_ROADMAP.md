# Matick Train — ruta de entrenamiento eficiente (inspiración funcional Unsloth)

Estado: propuesta técnica, **no motor de entrenamiento implementado**. Mantener Matick Studio LM Cloud independiente de LM Studio y no copiar código, marca ni interfaz de Unsloth.

## Experiencia de usuario objetivo
En Matick Work agregar una pestaña **Entrenar** con asistente de seis pasos:
1. Modelo base: identificador, arquitectura, licencia, formato y memoria estimada.
2. Datos: JSONL local, vista previa, separación train/validation, deduplicación y eliminación de secretos.
3. Técnica: LoRA/QLoRA, SFT y posteriormente DPO; indicar qué es compatible y qué requiere conversión.
4. Recursos: detectar CUDA y VRAM, RAM y CPU; no prometer aceleración NPU sin backend real.
5. Ejecución: progreso, pérdida train/eval, tokens/s, VRAM máxima, checkpoints y cancelar/reanudar.
6. Evaluación: pruebas de calidad, latencia, memoria y exportación reversible.

## Primera implementación viable (Windows 11, RTX 5060 8 GB, RAM 32 GB)
- **Worker separado del servidor cloud**, lanzado explícitamente por el usuario en su PC; el backend cloud no debe ejecutar comandos arbitrarios ni recibir archivos privados por defecto.
- Python y PyTorch compatibles con la arquitectura CUDA detectada; validar en CI y equipo real antes de declarar soporte.
- LoRA sobre modelo de 0.5B–1.7B inicialmente; QLoRA de 4B solo tras prueba de VRAM. bf16 si soportado, gradient checkpointing, microbatch 1, acumulación 8–16, longitud 512–1024; cuantización 4-bit solo si backend y GPU lo permiten.
- Pipeline con adaptadores de Transformers, PEFT, TRL y datasets; **Unsloth como adaptador opcional** sujeto a plataforma y licencia. No asumir que sus kernels funcionan en Windows nativo.
- Si el formato no es entrenable (p. ej. GGUF), informar y solicitar pesos originales compatibles; no fingir que una conversión recupera información perdida.
- La destilación teacher→student requiere modelo estudiante genuinamente menor y evaluación; cuantizar no reduce el número de parámetros.

## Seguridad y reversión
- Desactivado por defecto; solo loopback; autorización por ejecución, sin credenciales externas.
- Validar rutas dentro de un directorio de trabajo elegido, no seguir symlinks fuera de él, limitar tamaño de archivos y recursos.
- Prohibir scripts de entrenamiento aportados por datasets y evitar cargar checkpoints pickle no confiables.
- Registrar versión de dependencias, hash de datos, configuración y semilla; checkpoints atómicos.
- Entrenar adaptadores sin modificar pesos base; botón Restaurar selecciona checkpoint anterior, y Cancelar termina el worker sin borrar datos.
- Nunca fusionar automáticamente adaptadores ni sobrescribir modelos originales.

## Pruebas antes de integrar
1. Unitarias: configuración inválida, rutas, formato de datos, estimación de memoria y cancelación.
2. Integración CPU con modelo diminuto: 2 pasos SFT, checkpoint y reanudación.
3. Windows RTX 5060: medir VRAM pico, tokens/s y pérdida con y sin checkpointing.
4. Calidad: comparar respuestas del base vs adaptador en conjunto retenido; registrar regresiones.
5. Seguridad: token no aparece en logs; rutas externas y checkpoint no confiable rechazados.
6. CI: pruebas CPU sin descargar modelos grandes; GPU en ejecución manual y opt-in.

## Entregas
- Fase A: esquema de jobs, UI de configuración y simulación sin entrenamiento real.
- Fase B: worker SFT + LoRA funcional, pruebas y logs.
- Fase C: QLoRA, comparador de resultados y exportación.
- Fase D: destilación y poda estructural con benchmarks de calidad.
Cada fase debe permanecer etiquetada **pendiente** hasta existir commits, pruebas y ejecución comprobada.
