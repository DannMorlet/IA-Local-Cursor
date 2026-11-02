# Matick Studio LM — revisión técnica y funcional (2026-11-02)

## Evidencia del proyecto (PR #46)

- Error reproducido en GitHub Actions 41485507079: `cloud/tests/test_work.py::test_light_theme_reference_and_working_home_controls` exigía la cadena obsoleta `home-model-chip.textContent=id`, incompatible con el estado visible `Cargado / Falta cargar / Inferencia por verificar`. Se actualizó la aserción sin desactivar la verificación.
- Pruebas adicionales `cloud/tests/test_web_chat.mjs`: no autenticado, inventario caducado, modelo ausente, REST v1 sin instancia cargada, REST v1 con instancia declarada y proveedor compatible sin certificación de inferencia.
- El botón de envío no debe atribuir inferencia real al mero hecho de seleccionar un modelo. Para REST v1, la interfaz bloquea envío si el catálogo no informa instancias cargadas. Para proveedores OpenAI compatibles, el catálogo no demuestra residencia en VRAM ni ejecución local: la respuesta sigue marcada como *inferencia sin verificar*.
- Las pruebas del DOM y de handlers son estáticas, no equivalen a clics automatizados en un navegador real. El inventario de botones aún requiere pruebas visuales de teclado/foco/errores en un navegador y pruebas en Windows x64.
- El runtime independiente con pesos reales, tokens/s, VRAM de RTX 5060 y calidad de destilación siguen **SIN PROBAR**.
- Reversión: revertir commits del PR; sin migraciones ni acceso a `C:\IA\Matick Studio LM`.

## Investigación de fuentes oficiales y decisiones aplicables

| Fuente oficial | Hallazgo aplicable | Decisión en Matick | Límite |
| --- | --- | --- | --- |
| [Hugging Face PEFT — LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora) | Adaptadores de bajo rango entrenan menos parámetros; `merge_and_unload()` fusiona adaptador con base. | Entrenamiento LoRA opcional y aislado del núcleo; medir memoria, tiempo y calidad. | No reduce automáticamente el número de parámetros de la red base. |
| [Hugging Face TRL — SFTTrainer](https://huggingface.co/docs/trl/sft_trainer) | Soporta `peft_config`, datasets de entrenamiento/evaluación y QLoRA mediante configuración de cuantización. | Probar en entorno separado con datasets pequeños y semilla fija. | Sin benchmark maestro/estudiante no afirmar retención de calidad >=90%. |
| [Unsloth — repositorio oficial](https://github.com/unslothai/unsloth) | Referencia de técnicas de entrenamiento y experiencia de usuario en Windows. El repositorio presenta archivos bajo licencias Apache-2.0 y AGPL-3.0. | Solo comparar técnicas y medir; **no copiar** código, UI, assets ni incorporar dependencias sin auditoría de licencia por archivo. | La compatibilidad y licencia de cada componente requieren verificación antes de redistribuir. |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | Motor C/C++ con herramientas de conversión a GGUF y licencia MIT declarada. | Evaluar integración *opcional* y aislada o formato GGUF, con atribución/licencias y pruebas de ejecución. | Una integración externa no equivale a un motor de inferencia original. |
| [Microsoft — Direct3D 12](https://learn.microsoft.com/en-us/windows/win32/direct3d12/directx-12-programming-guide) | Guías oficiales de sincronización, residencia de memoria y depuración GPU. | Mantener DX12 + fallback GDI y medir tiempos de arranque, errores DRED y VRAM en hardware real. | Compilar DX12 en CI no demuestra renderizado ni inferencia en RTX 5060. |

## Distinción entre reducción real y compresión

- **Poda estructural o destilación maestro/estudiante:** puede reducir realmente la cantidad de parámetros si se crea y valida un estudiante de menor tamaño.
- **Cuantización GGUF:** reduce bytes de pesos y uso de memoria; no equivale por sí misma a eliminar parámetros.
- **LoRA/QLoRA:** reduce parámetros *entrenables* y/o memoria de ajuste; no demuestra un modelo base más pequeño.
- **Calidad retenida >=90%:** solo aprobada si `puntuación_estudiante / puntuación_maestro >= 0.90` sobre un conjunto de evaluación definido, mismo protocolo y métricas documentadas; si el maestro puntúa cero, la razón no es evaluable. Incluir resultados por dominio, latencia y VRAM, no solo promedio.

## Estado frente al informe anterior

La última referencia confirmada en `main` es PR #45 (rechazo de NaN/Infinity en eventos). Este documento añade el diagnóstico de la UI y criterios de preparación de modelos del PR #46. No se localizó una bitácora previa de investigación con el mismo alcance para calcular diferencias metodológicas más antiguas.

## Referencia adicional no disponible

Se intentó abrir https://chatgpt.com/share/6ae8bd76-7e50-83e8-b56a-603f6e766ba8 y el acceso devolvió error; no se extrajeron requisitos de ese enlace ni se inventó su contenido.
