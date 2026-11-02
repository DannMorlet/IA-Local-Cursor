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

## Seguimiento incremental: carga asíncrona y verificación de estado (PR #46)

- **Fallo adicional corregido:** la interfaz mostraba `Modelo cargado en el motor conectado` apenas `POST /v1/models/load` respondía, aunque la instancia todavía no figurara en `GET /v1/models`. La aceptación de la solicitud no es prueba de carga real.
- **Cambio:** se vuelve a consultar el inventario tras la petición; los mensajes distinguen `carga solicitada`, `instancia declarada cargada`, `estado no verificable` y `proveedor compatible sin inferencia acreditada`. Mientras se refresca el inventario, `inventoryFresh=false` bloquea nuevos envíos basados en un catálogo anterior.
- **Pruebas agregadas:** `cloud/tests/test_web_chat.mjs` cubre cinco estados de confirmación y `cloud/tests/test_work.py` impide recuperar el aviso engañoso. Aún no se ha probado una carga real de pesos, ni la latencia o VRAM de RTX 5060.
- **Reversión:** revertir los commits de este PR; no se cambió la API, el esquema SQLite, el instalador, DX12 ni GDI.

### Fuentes oficiales revisadas y comparación con el informe anterior

- [PEFT LoRA, documentación oficial](https://huggingface.co/docs/peft/main/package_reference/lora): `merge_and_unload()` produce un modelo base+adaptador fusionado, pero no elimina por sí solo parámetros de la arquitectura base; la guía advierte que fusionar solo algunos adaptadores activos puede omitir otros. **Decisión:** no introducir fusión automática en el núcleo; diseñar una tarea opcional con verificación explícita de adaptadores y benchmark maestro/estudiante.
- [PyTorch `torch.compile`](https://docs.pytorch.org/docs/stable/generated/torch.compile.html): recompilaciones por cambios de guardas y límites de recompilación pueden generar costos de arranque. **Decisión:** cualquier experimento de compilación será opcional, con mediciones de arranque en frío y tiempo de inferencia; no añadirlo a la UI principal sin evidencia.
- [llama.cpp, versiones oficiales](https://github.com/ggml-org/llama.cpp/releases): existen artefactos Windows x64 CPU/CUDA/Vulkan. **Decisión:** investigar una sonda GGUF externa y aislada, con verificación de licencias y rendimiento; no llamar `motor propio` a un runtime ajeno.
- [Unsloth, repositorio oficial](https://github.com/unslothai/unsloth): distingue paquete central Apache-2.0 de componentes opcionales de UI AGPL-3.0. **Decisión:** mantener consulta documental exclusivamente; no copiar código, diseño ni recursos.

**Diferencia concreta respecto al informe anterior:** se resolvió una afirmación engañosa sobre carga de modelos con pruebas automáticas; no se incorporaron dependencias, motores externos ni técnicas de entrenamiento. La retención de calidad >=90% sigue SIN PROBAR. El chat compartido continúa inaccesible en esta revisión; no se atribuyen requisitos a su contenido.


## Ejecución incremental: inventarios concurrentes y destilación documentada (2026-11-02)

### Error de interfaz corregido en esta ejecución

- **Condición reproducible en el código:** dos llamadas solapadas a `refreshModels()` podían resolverse fuera de orden. La respuesta más antigua sobrescribía el catálogo reciente, la selección y `inventoryFresh`; un error tardío también podía invalidar el catálogo recién cargado.
- **Corrección implementada:** contador monotónico `inventoryRequestId` y comparación del token de la sesión. Solo la consulta más reciente de la sesión actual puede cambiar inventario, selección, indicadores o mensajes de error. No se añadió dependencia.
- **Pruebas:** dos tests Node para respuesta/error obsoleto y cambio de sesión; guardia de integración estática Python. La prueba unitaria del guardia no sustituye una prueba visual real con latencia de red artificial.
- **Reversión:** revertir los commits de esta sección del PR #46. No cambia el contrato REST v1, la base SQLite, el instalador ni archivos locales del usuario.

### Investigación técnica nueva frente a la revisión anterior

- [TRL DistillationTrainer (oficial)](https://huggingface.co/docs/trl/distillation_trainer): además de `SFTTrainer`, TRL documenta **destilación on-policy maestro/estudiante** con divergencia Jensen-Shannon calculada por fragmentos para reducir memoria de activaciones. Requiere compatibilidad de vocabulario entre maestro y estudiante; permite `peft_config` opcional. **Novedad frente al informe previo:** investigar una prueba aislada de `DistillationTrainer`, sin incorporarlo al núcleo ni ejecutarlo en CI ligero.
- [TRL AsyncDistillationTrainer](https://huggingface.co/docs/trl/distillation_trainer): la documentación enlaza una variante con maestro servido por HTTP; podría evitar cargar maestro y estudiante simultáneamente en la RTX 5060 de 8 GB, pero **su viabilidad y latencia aún no están medidas**. No habilitar acceso remoto, credenciales ni costes por defecto.
- [PEFT LoRA (oficial)](https://huggingface.co/docs/peft/main/package_reference/lora): `merge_and_unload()` fusiona pesos de adaptadores con el modelo base; **no reduce la arquitectura ni el número de parámetros**. Sin cambio de decisión respecto al informe previo.
- [llama.cpp (oficial)](https://github.com/ggml-org/llama.cpp): motor C/C++ con formato GGUF y licencia MIT. Mantener como referencia para una integración externa opcional y atribuida; **no** afirmar motor propio ni copiar código.
- [Unsloth (oficial)](https://github.com/unslothai/unsloth): mantiene distinción de licencias Apache-2.0/AGPL-3.0 por componentes. Solo consulta comparativa, sin copiar UI, assets o código.
- [Microsoft Direct3D 12 (oficial)](https://learn.microsoft.com/en-us/windows/win32/direct3d12/directx-12-programming-guide): sincronización y residencia GPU requieren comprobación en dispositivo; mantener GDI de respaldo. No se cambia la ruta de renderizado.
- [PyTorch torch.compile (oficial)](https://docs.pytorch.org/docs/stable/generated/torch.compile.html): evitar costes de compilación/recompilación en arranque de la UI; no incorporarlo al núcleo sin mediciones.

**Criterios pendientes:** probar todos los botones, foco y accesibilidad en navegador/Windows reales; confirmar carga de pesos y tokens/s; medir VRAM; aprobar destilación solo con conjunto de evaluación reproducible y razón estudiante/maestro >=0.90. El chat compartido devolvió HTML sin contenido legible en esta ejecución: no se atribuyen requisitos nuevos.


## Ejecución incremental: autenticación cancelada y sesiones existentes (2026-11-02)

### Bug funcional de interfaz

- **Hallazgo en código:** el formulario asignaba el token de la sesión *antes* de validar /v1/capabilities. Cancelar el modal durante una petición lenta no impedía que una respuesta tardía autenticara la sesión; un intento fallido borraba además un token válido previo y dejaba el indicador «Conectado» desincronizado.
- **Cambio real:** /v1/capabilities recibe el token candidato sin reemplazar la sesión activa. El botón **Entrar** se deshabilita durante la comprobación; **Cancelar/Esc** y editar el token invalidan el intento mediante un identificador monotónico. Solo el último intento vigente puede activar sesión. Los fallos conservan la sesión previamente autenticada.
- **Pruebas agregadas:** Node comprueba intentos cancelados/editados y rechazo de resultados tardíos; Python inspecciona la conexión entre formulario, token candidato y guardia. Estas pruebas **no son** un smoke test visual con navegador real; el caso de carrera completo debe repetirse con red lenta en un navegador.
- **Reversión:** revertir los commits de esta sección del PR #46. Sin cambios a REST v1, SQLite, instalador, DX12/GDI ni a rutas locales del usuario.

### Comparación técnica con la revisión previa y fuentes oficiales

| Fuente | Diferencia comprobada frente a revisión anterior | Decisión y límite |
| --- | --- | --- |
| [TRL GOLD Trainer](https://huggingface.co/docs/trl/gold_trainer) | **Nueva opción identificada:** destilación entre maestro y estudiante con tokenizadores diferentes mediante alineación de fragmentos de texto. La API está en el módulo experimental. | Evaluar solo en entorno opcional, con tests de alineación, memoria y licencia; no integrarlo en el núcleo ni prometer 90% de calidad. |
| [TRL DistillationTrainer](https://huggingface.co/docs/trl/distillation_trainer) | Se confirma la alternativa on-policy y el maestro remoto/asíncrono documentados previamente; no constituye un benchmark. | Mantener investigación, sin entrenar en CI ligero ni enviar datos fuera del equipo sin consentimiento. |
| [PEFT Quantization](https://huggingface.co/docs/peft/developer_guides/quantization) | QLoRA combina pesos cuantizados con adaptadores entrenables. | Reducir memoria de ajuste no equivale a disminuir número de parámetros; exigir estudiante menor y benchmark reproducible. |
| [Unsloth](https://github.com/unslothai/unsloth) | Distinción Apache-2.0 para núcleo y AGPL-3.0 para ciertas partes de UI. | Solo referencia documental; no se copió código ni recursos. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Referencia MIT y GGUF para inferencia externa opcional. | No presentar como motor original de Matick ni añadirlo como dependencia obligatoria. |
| [PyTorch torch.compile](https://docs.pytorch.org/docs/stable/generated/torch.compile.html) | Sin cambio respecto a costes de compilación y arranque. | Medir arranque en frío antes de habilitarlo; no se incorporó. |
| [Microsoft Direct3D 12](https://learn.microsoft.com/en-us/windows/win32/direct3d12/directx-12-programming-guide) | Documenta validación GPU, residencia y DRED; no demuestra ejecución en RTX 5060. | Conservar DX12 y fallback GDI, pendientes pruebas físicas. |

El chat compartido https://chatgpt.com/share/6ae8bd76-7e50-83e8-b56a-603f6e766ba8 volvió a devolver error de acceso; no se infirieron requisitos nuevos. **Pendientes:** pruebas visuales de todos los botones y foco/teclado, reconexión con red lenta, inferencia real con pesos, VRAM/tokens/s y benchmark de retención >=90%.


## Ejecución incremental: limpiar conversación durante generación (2026-11-02)

### Bug funcional y corrección
- **Antes:** al pulsar «Nueva conversación» mientras `POST /v1/chat` estaba pendiente, el chat se vaciaba, pero «Enviar» y el envío desde la portada permanecían deshabilitados hasta finalizar la solicitud anterior. Si esa solicitud tardaba, la conversación nueva parecía bloqueada. El mismo problema podía ocurrir al cambiar de modelo.
- **Después:** limpiar la conversación, cambiar de modelo o perder la selección restablece inmediatamente ambos controles de envío. La cláusula `finally` solo puede habilitarlos si pertenece al `chatEpoch` vigente; así, una respuesta antigua no desbloquea un envío posterior. Las respuestas antiguas ya se descartaban mediante el mismo contador.
- **Pruebas añadidas:** dos casos Node con promesas/control de orden que comprueban reinicio y respuesta tardía, más aserciones de integración estática Python. **No equivalen a pruebas de clics reales ni prueban cancelación de red**: el HTTP anterior puede continuar en el servidor.
- **Reversión:** revertir commits de este cambio; no cambia endpoints, instalador, Windows DX12/GDI, base de datos ni dependencias. No se accedió a `C:\\IA\\Matick Studio LM`.

### Comparación técnica con el informe previo (fuentes oficiales)
- [PyTorch: reducir tiempo de compilación](https://docs.pytorch.org/docs/2.15/user_guide/torch_compiler/compile/programming_model.reducing_compile_time.html): el arranque en frío de `torch.compile` puede costar segundos o minutos y las recompilaciones lo empeoran. **Decisión nueva:** mantener compilación JIT fuera del arranque obligatorio de la interfaz blanca; medir por separado cold start y latencia sostenida antes de activarla.
- [TRL: DistillationTrainer](https://huggingface.co/docs/trl/main/distillation_trainer): admite maestro externo y entrenamiento opcional del estudiante con PEFT, pero la documentación de `main` requiere versión de origen y las interfaces pueden evolucionar. **Decisión:** aislar cualquier prototipo en entorno opcional, fijar versiones y no prometer ejecución simultánea en 8 GB.
- [PEFT: fusión LoRA](https://huggingface.co/docs/peft/main/package_reference/lora): `merge_and_unload` fusiona adaptadores, sin reducir automáticamente parámetros base. **Sin cambio** respecto al informe anterior; la meta de calidad >=90% requiere benchmarks independientes.
- [llama.cpp](https://github.com/ggml-org/llama.cpp): GGUF y backends Windows son referencia de interoperabilidad, no evidencia de un motor original de Matick. **Sin incorporación** ni redistribución.
- [Unsloth](https://github.com/unslothai/unsloth): licencias Apache-2.0 y AGPL-3.0 según componente. **Solo referencia documental**, sin copiar código ni assets.
- [Microsoft DRED](https://learn.microsoft.com/windows/win32/direct3d12/use-dred): breadcrumbs y reportes de fallos GPU pueden mejorar logs DX12. **Candidato futuro** tras resolver botones y carga de modelos; no implementado aquí.

**Diferencia comprobable:** se corrigió un bloqueo de los botones del chat al reiniciar la conversación, no una capacidad de inferencia ni destilación. La referencia https://chatgpt.com/share/6ae8bd76-7e50-83e8-b56a-603f6e766ba8 volvió a fallar al abrirse; no se extrajeron requisitos. PC real RTX 5060, smoke visual, pesos cargados, MCP en hardware y calidad retenida >=90% siguen **SIN PROBAR**.
