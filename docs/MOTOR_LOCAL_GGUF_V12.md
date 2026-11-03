# Matick Studio LM v1.2 · Inferencia local GGUF (fase de integración)

Matick tiene un **controlador propio** de procesos de inferencia que ejecuta `llama-server` de [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp); el modelo no pasa por LM Studio ni Unsloth. El binario y los pesos **no están incluidos** en el instalador ligero por su tamaño y dependencias. Es una integración funcional de software, **no** una prueba de calidad/velocidad con pesos reales ni de CUDA en la RTX 5060.

## Ruta Windows 11 x64

La instalación de Matick y su carpeta de trabajo son conceptos distintos. El motor local buscará automáticamente:
- Ejecutable: `C:\IA\Matick Studio LM\engine\llama-server.exe`
- Archivos GGUF: `C:\IA\Matick Studio LM\models\` (puede contener subcarpetas)
- Registros de error: `%LOCALAPPDATA%\MatickStudioLM\logs\llama-inference.log`
- Base de datos, proyectos y modelos anteriores: no se borran ni se migran automáticamente.

Coloca **un paquete oficial de llama.cpp para Windows x64** (con sus DLL necesarias en `engine`) y modelos **GGUF compatibles** en `models`. No coloques en la carpeta `models` archivos de pesos Hugging Face que no sean GGUF; ese formato requiere otra ruta de inferencia o conversión. Consulta los [releases oficiales de llama.cpp](https://github.com/ggml-org/llama.cpp/releases) y comprueba hashes, Windows y CUDA. Nunca descargues ni instales drivers NVIDIA sin autorización.

Si ya guardas GGUF en otra carpeta, no dupliques decenas de GB: configura su ruta explícita como `MATICK_LOCAL_MODELS_DIR`. Para seleccionar el motor aunque falte su ejecutable, usa `MATICK_INFERENCE_BACKEND=local`; esto informa del error en la interfaz en lugar de atribuir inferencia a un proveedor externo. El modo `auto` utiliza llama.cpp cuando existe el ejecutable y no se configura un servidor REST v1 externo. Con `MATICK_INFERENCE_BACKEND=external` puedes conservar el modo alternativo actual.

En PowerShell (ejemplo para una terminal de prueba):
```powershell
$env:MATICK_INFERENCE_BACKEND = 'local'
$env:MATICK_HOME = 'C:\IA\Matick Studio LM'
$env:MATICK_LOCAL_MODELS_DIR = 'C:\IA\Matick Studio LM\models'
# Opcional si colocaste llama-server.exe en otra ruta:
# $env:MATICK_LLAMA_SERVER = 'D:\Herramientas\llama.cpp\llama-server.exe'
```

## Funcionamiento de los botones

1. **Actualizar modelos:** enumera hasta 300 GGUF de la carpeta designada, sin seguir enlaces fuera de ella. Muestra nombres, tamaños en GiB e indicador de instancia cargada.
2. **Guardar ajustes:** persiste el modelo seleccionado y los parámetros en SQLite. Guardar no equivale a cargar pesos.
3. **Cargar:** inicia un proceso hijo `llama-server` escuchando solo en 127.0.0.1 con clave aleatoria, valida `/health` y el catálogo `/v1/models`, y confirma el modelo. Ajustes: contexto, lote, Flash Attention y offload KV; el ajuste automático de GPU permite al motor decidir según VRAM disponible.
4. **Chat:** envía historial y parámetros admitidos al proceso local, verifica que la respuesta tenga texto y nombre de modelo. No presenta un HTTP 200 vacío como inferencia.
5. **Descargar RAM:** termina **solo** el proceso que inició Matick; no elimina el archivo GGUF ni modifica otras aplicaciones.
6. **Descargar modelo nuevo:** desactivado en modo local; no instala binarios/pesos sin permiso. Las sesiones stateful de REST v1 se desactivan en modo GGUF: el contexto se transmite con el historial del chat.

Solo se carga un modelo a la vez; los parámetros incompatibles dan un error explícito. El motor local necesita GGUF compatible con la versión de llama.cpp instalada. Si no hay memoria suficiente, verifica los logs y prueba un GGUF cuantizado más pequeño; no afirmamos que todo modelo entrará en 8 GB VRAM.

## Verificación antes de publicar

CI incluye pruebas HTTP extremo a extremo con **un servidor simulado** que se comporta como llama.cpp; no prueba pesos reales. Requisitos para dar por completado en tu Windows:
- Instalar paquete Windows x64 con `local_engine.py` y comprobar que abre Work y modelos;
- Abrir un GGUF real en `C:\IA\Matick Studio LM\models` y observar proceso, logs, tiempos y consumo de VRAM;
- Enviar dos preguntas, cambiar de modelo y descargarlo sin pérdida de archivos;
- Medir tokens/s reales (si están disponibles), no solo tiempo HTTP;
- Validar DirectX 12, escalado DPI y botones en la pantalla física.

Si la versión de llama.cpp rechaza una bandera de lanzamiento, usa el archivo de log para comprobar incompatibilidad; no desactives silenciosamente ajustes para simular un éxito.
