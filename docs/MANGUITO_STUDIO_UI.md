# Manguito Studio v0.2 — guía del diseño y ejecución

## Qué es

Vista de escritorio experimental para acompañar al Manguito.exe original. No lo reemplaza, no extrae sus herramientas y no borra tus 32 GB de modelos ni entrenamientos.

El Manguito.exe compartido es PE32+ .NET WinForms con referencias a WebView2, LM Studio y NVIDIA. El proyecto nuevo conserva esa dirección tecnológica y agrega un servidor Python sin dependencias runtime (salvo para empaquetar) y una interfaz HTML/CSS/JS completamente local.

## Funciones hoy

| Área | Disponible |
|---|---|
| Ventana nativa Windows | Sí, compilable mediante .NET 8 WinForms + WebView2 |
| Dashboard responsive y temas | Sí |
| Chat de texto con LM Studio u otro servidor OpenAI-compatible | Sí, si el modelo está cargado |
| Ver modelos disponibles | Sí, cuando responde el servidor local |
| Listado, lectura y propuesta de edición de texto | Sí, limitado al workspace |
| Escribir archivos | Solo en modo Python con bandera de escritura y aprobación local |
| Grabar pantalla, mover mouse, ejecutar comandos | NO, aún no |
| GPU/NPU, CoffinU, ComfyUI, subagentes | En investigación y desarrollo; no conectados |
| Móvil y Galaxy Fit3 | En planificación; NO se permite acceso remoto público |

## Edición nativa recomendada

1. Abre las Actions de la rama feature/manguito-hybrid-foundation.
2. En el workflow Manguito Studio · build windows, descarga el artefacto Manguito-Studio-Windows-preview (ZIP).
3. Extrae todos sus archivos en una carpeta propia. Deben quedar juntos Manguito-Studio.exe y Manguito-Backend.exe.
4. Inicia Manguito-Studio.exe. La app levanta su backend en loopback 127.0.0.1:8765, crea un workspace en AppData local y conecta WebView2 con token de sesión creado al vuelo.
5. Si deseas chat, abre LM Studio, carga un modelo y activa su servidor local compatible con OpenAI en 127.0.0.1:1234/v1. Haz clic en actualizar.
6. Cierra la app para terminar el proceso hijo del backend.

La compilación Windows se realiza en GitHub Actions; por ahora no hay prueba directa de la ejecución en tu PC. El paquete puede requerir el runtime WebView2 Evergreen de Microsoft, normalmente disponible en Windows 11.

## Edición portable alterna

El artefacto Manguito-Portable-Windows-preview contiene un solo exe de consola. Inicia el mismo servidor y abre el navegador predeterminado en localhost. Copia el token que se muestra en la consola y pulsa Conectar.

Si prefieres Python sin empaquetar, en la raíz del repositorio ejecuta:

    python -m manguito.desktop

Eso crea una carpeta ~/ManguitoWorkspace, muestra el token de sesión y abre el navegador.

## Edición autorizada de archivos

La ventana nativa es intencionalmente de solo lectura; así no hay cambios de archivos accidentales. Para probar propuestas y aplicaciones desde Python, antes de iniciar:

    $env:MANGUITO_ENABLE_WRITES = "1"
    python -m manguito.desktop

El programa imprimirá un código de aprobación distinto del token principal. No lo compartas ni lo pegues en chats. Revisa primero las diferencias de los archivos antes de aplicar cambios. Solo se permiten rutas de un workspace fijo.

## Diseño visual

Paleta principal verde menta + grafito, acentos lavanda y naranja, transiciones discretas y composición apta para escritorio y teléfono. Módulos previstos: agente de programación, enrutador GPU/NPU, CoffinU, generación multimedia y controles remotos de baja latencia. Las tarjetas no disponibles se distinguen como PRÓXIMAMENTE.

El navegador no utiliza dependencias CSS o JavaScript externas. Los mensajes del modelo se insertan como texto (no HTML), token solo en sesión, CSP restrictiva y servidor local con Bearer.

## Compatibilidad y próximos pasos

- Original Manguito.exe: sin modificar.
- Equipo objetivo: RTX 5060 8 GB VRAM, Core Ultra 5 225F, 32 GB DDR5-6000, Windows 11.
- Antes de integrar automatización total, agregar inventario de ventanas, captura con permiso, telemetría GPU real, agentes de código y registro con deshacer.
- No publicar claves, modelos de 32 GB ni datos personales dentro de la rama pública.
- GitHub main actualmente contiene un proyecto Matick Cloud diferente. No fusionar esta rama automáticamente: decidir primero cómo se separarán ambos productos en repositorios o rutas.
