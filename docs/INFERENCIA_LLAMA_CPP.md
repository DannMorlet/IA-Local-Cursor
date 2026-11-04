# Motor local GGUF para Matick Studio LM: llama.cpp

**Estado (2026-11-04): código integrado en esta rama; inferencia real en Windows aún pendiente de verificar.** El archivo EXE DX12 por sí solo no incorpora pesos ni motor.

## Arquitectura
Matick Studio LM es independiente de LM Studio. Matick Core (Python embebido) arranca, cuando existe configuración autorizada, un proceso hijo oficial llama-server.exe. El puente HTTP OpenAI-compatible de Matick consulta ese proceso únicamente en http://127.0.0.1:18776/v1/chat/completions, usando alias matick-local. La interfaz sigue con DirectX 12; **el cálculo de IA usa CUDA o Vulkan, no DirectX 12**.

El proceso local se detiene al cerrar Matick Core y queda cubierto por el Job Object del lanzador, si fue iniciado mediante el EXE empaquetado. Sin archivo de configuración no se inicia ni se reserva VRAM. Una configuración explícita del proveedor MATICK_MODEL_BASE_URL/MATICK_MODEL_ID tiene prioridad y no se sobreescribe.

## Descarga oficial verificada
Origen: https://github.com/ggml-org/llama.cpp/releases . Versión de prueba fijada: b12099 del 4 noviembre de 2026, pre-release.

Se descargan ZIPs oficiales con SHA256 fijos, se extraen dentro de la carpeta local del usuario y se conserva un respaldo de la configuración al reemplazarla.

- Cuda13: llama-b12099-bin-win-cuda-13.4-x64.zip y cudart-llama-bin-win-cuda-13.4-x64.zip; recomendado para RTX 5060 **solo si el driver es compatible**.
- Vulkan: llama-b12099-bin-win-vulkan-x64.zip; alternativa cuando CUDA falle.
- Cpu: llama-b12099-bin-win-cpu-x64.zip; respaldo y pruebas de diagnóstico.

Nunca instalar drivers NVIDIA sin permiso. No descargar modelos automáticamente y no modificar LM Studio.

## Instalación Windows x64
En una **copia de trabajo de esta rama**, con PowerShell 5.1+, usa un GGUF que tengas realmente guardado. Ejemplo (reemplaza el nombre por tu ruta):

    .\tools\install_llamacpp_engine.ps1 -Backend Cuda13 -ModelPath 'C:\IA\Modelos\MI_MODELO.gguf'

Alternativas:

    .\tools\install_llamacpp_engine.ps1 -Backend Vulkan -ModelPath 'D:\Modelos\MI_MODELO.gguf'
    .\tools\install_llamacpp_engine.ps1 -Backend Cpu -ModelPath 'D:\Modelos\MI_MODELO.gguf' -GpuLayers 0
    .\tools\install_llamacpp_engine.ps1 -Backend Cuda13 -ModelPath 'D:\Modelos\MI_MODELO.gguf' -GpuLayers 20 -ContextSize 2048

El instalador verifica la cabecera GGUF, los hashes de los archivos oficiales, conserva el archivo .gguf original y crea:

- %LOCALAPPDATA%\MatickStudioLM\inference.json
- %LOCALAPPDATA%\MatickStudioLM\engines\b12099-cuda13\ (o vulkan/cpu)
- %LOCALAPPDATA%\MatickStudioLM\logs\llama-inference.log

**Importante:** para que funcione al abrir la app, usa el nuevo paquete Windows, que debe incluir cloud/matick_cloud/local_inference.py. El exe anterior adjuntado por sí solo no tiene esta capacidad. El instalador NO reemplaza C:\IA\Matick Studio LM ni modifica Program Files.

Espera la carga del GGUF y comprueba desde otra terminal:

    Invoke-RestMethod http://127.0.0.1:18776/health

El modelo puede responder temporalmente 503 mientras carga. Un HTTP 200 no prueba por sí solo inferencia: enviar un prompt de chat y medir tokens/s, VRAM y estabilidad.

## Seguridad y límites
Solo se permite un ejecutable llamado llama-server.exe dentro de %LOCALAPPDATA%\MatickStudioLM\engines. Si el puerto 18776 está ocupado, Matick no se conecta al servicio ajeno ni lo reemplaza. Ningún proceso de usuario o servidor LM Studio se termina por este cambio.

Las pruebas CI verifican la configuración, restricciones y ciclo de vida con mocks, **no** un modelo real. La compilación final y las pruebas de compatibilidad CUDA y GGUF deberán efectuarse en Windows.

## Desactivar y revertir
Cierra Matick y establece enabled: false en inference.json, o restaura la copia con sufijo .backup-YYYYMMDD-HHMMSS. El ejecutable oficial queda en engines y puede eliminarse mientras Matick esté cerrado. Tu GGUF, drivers y otras instalaciones se conservan.

## Prueba aislada del contrato

    $env:PYTHONPATH = 'cloud'
    python -m unittest discover -s cloud/tests -p test_local_inference.py -v
