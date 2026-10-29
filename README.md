# IA-Local-Cursor — Manguito IA híbrida 🥭

Proyecto experimental de asistentes locales, agentes de desarrollo y control del PC de DannMorlet. Integra de forma gradual modelos locales (LM Studio), herramientas del sistema, exploración de archivos, generación multimedia, NPU/GPU, conexión móvil y respaldo opcional en la nube.

## Equipo objetivo

- Windows 11 26H2
- Intel Core Ultra 5 225F: NPU Intel AI Boost, 13 TOPS INT8 oficiales
- NVIDIA GeForce RTX 5060, 8 GB de VRAM (dato proporcionado por el usuario)
- 32 GB DDR5-6000 (2 x 16 GB)
- Teléfono Android y pulsera Samsung Galaxy Fit3

## Estado actual

**v0.1.0 — prototipo, NO instalador ni acceso completo al PC**. Esta rama ofrece una pasarela Python estándar, sin dependencias externas, que únicamente escucha en 127.0.0.1:

- GET /v1/status — estado del proceso
- GET /v1/models — modelos del servidor compatible con OpenAI
- POST /v1/chat — chat textual local con LM Studio (u otro backend compatible)
- GET /v1/fs/list?path=. — listar hasta 200 entradas de carpeta autorizada
- GET /v1/fs/read?path=archivo.txt — leer archivos de texto de hasta 256 KiB
- POST /v1/fs/propose — propuesta de edición en diff unificado
- POST /v1/fs/apply — aplicar edición solo si el PC habilitó escrituras y se proporcionó el código temporal local

Toda solicitud requiere el encabezado Authorization: Bearer TOKEN. No existe ejecución de shell, grabación de pantalla, control de ratón, acceso remoto público, audio ni instalación automática en esta versión. Las pruebas de CI verifican el módulo, pero la instalación real se debe comprobar en el PC.

## Inicio en Windows

1. Instala Python 3.12 o posterior y LM Studio. Carga el modelo local y en LM Studio Developer activa Start server; el servidor compatible debería escuchar en 127.0.0.1:1234/v1.
2. Clona el repositorio o descárgalo en ZIP y abre PowerShell en la carpeta raíz.
3. Ejecuta: powershell -ExecutionPolicy Bypass -File .\\scripts\\start-manguito.ps1
4. El script crea un directorio de pruebas bajo tu perfil (no modifica tus carpetas personales). Imprime el token local de esta sesión. No lo publiques ni lo subas a GitHub.
5. Para comprobar el servidor desde PowerShell en otra ventana:

   Invoke-RestMethod -Headers @{Authorization = "Bearer $env:MANGUITO_TOKEN"} -Uri http://127.0.0.1:8765/v1/status

   Nota: las variables de entorno de una sesión no se comparten con otras ventanas. Para pruebas usa la MISMA ventana o configura tú el token en ambas. No copies el token en chats públicos.

6. Pruebas: python -m unittest discover -s tests -v

Por defecto los cambios a archivos están DESACTIVADOS. En el PC puedes habilitarlos con el parámetro -AllowWrites al iniciar el script; aun así cada escritura requiere aprobación local. No se modifica el registro de Windows ni se ejecutan órdenes arbitrarias.

## Plan técnico

- [Investigación, hardware y tecnologías](docs/INVESTIGACION.md)
- [Arquitectura y fases](docs/ARQUITECTURA.md)
- [Registro inicial del hardware](scripts/diagnostico-hardware.ps1)

Prioridad de experiencia móvil: Sunshine en Windows + Moonlight en Android para escritorio/juegos táctiles de baja latencia; la IA y los agentes van por otro canal con confirmaciones y registros.

Este repositorio ya posee una licencia Apache 2.0. No almacenar contraseñas, tokens, datos personales ni los ~32 GB de modelos en Git convencional. Usar archivos de pesos externos o Git LFS cuando corresponda, cuidando los límites y costos.

## Advertencia

Manguito no debe operar con privilegios administrativos de forma permanente ni ejecutar cambios destructivos sin aprobación verificable. Conducir motocicleta requiere atención total: no usar control remoto, pantallas ni interacciones de trabajo durante la conducción.
