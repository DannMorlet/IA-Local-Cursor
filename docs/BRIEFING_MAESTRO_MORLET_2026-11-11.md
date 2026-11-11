# Briefing maestro de Morlet para GPT Codex, Claude Code y Gemini
**Fecha de acuerdos:** 11 de noviembre de 2026  
**Propósito:** conservar instrucciones y decisiones de conversaciones de Morlet con GPT.  
**Estado:** DOCUMENTACIÓN; no confundir con app instalada, PR fusionado o pruebas del PC.

> **Regla principal:** cuando Morlet diga «continúa el proyecto», primero leer esta guía y las especificaciones; actuar solo sobre la tarea solicitada y con los permisos reales disponibles. El documento **no autoriza automáticamente** instalar software, borrar archivos, gastar créditos, cambiar proveedores ni editar Windows.

## A. Intención de Morlet

Morlet busca un ecosistema de IA local fácil de usar, en **español mexicano**, que funcione tanto en Windows como en sus apps relacionadas, conservando el trabajo entre sesiones y aprendiendo de errores. Quiere que su agente trabaje como un buen agente de programación: **investigue, edite, compile, detecte fallos, corrija y repita sin pedir indicaciones sobre cada error**, pero con límites de seguridad, verificaciones y control de costo. Prefiere dirigir proyectos, no supervisar cada línea.

En discusiones simuladas, usar los nombres **«Morlet»** y **«GPT»** para dos agentes ficticios; Morlet se representa en voz masculina natural y GPT en femenina natural, con pausas claras *entre turnos*, sin dramatización exagerada. Es una preferencia narrativa, no una capacidad garantizada de cambio de voz en ChatGPT.

## B. Productos (mantener distintos)

- **Matick Studio LM (Windows)**: producto principal. Chat centrado, experiencia sencilla, motores de inferencia/conexiones, diagnóstico, rendimiento y coordinación de tareas. No es lo mismo que **LM Studio**, que puede servir como un backend local.
- **Matick Studio LM Cloud**: desarrollo conectado y repositorio `DannMorlet/IA-Local-Cursor` (este). Decidir arquitectura exacta y compatibilidad con Windows, priorizando resultados verificables.
- **Matick Codex**: agente/programador propio, con supervisor ligero, herramientas controladas, pruebas, historial persistente, router de modelos y escalado por excepción. Puede formar parte del ecosistema de Studio LM, sin confundir los nombres.
- **Morlet Reloj**: app Android distinta (mini mascota Clare y reloj/integraciones). Mantener código, pruebas y repositorio separados.
- **Manguito**: entrenamiento, destilación, cuantización, fusión y optimización; proyecto separado. 
- **Fresita Studio, gaming, Alexa y experimentos**: proyectos independientes. No trasladar archivos ni permisos sin petición.
- **`DannMorlet/Pruebas`**: laboratorio. [PR #6](https://github.com/DannMorlet/Pruebas/pull/6) contiene un prototipo experimental de memoria SQLite/NPU, **no** es el producto en producción.

## C. Capacidades de hardware discutidas

- Windows 11; Intel **Core Ultra 5 225F** con NPU de **13 TOPS INT8 nominales**; tarjeta NVIDIA RTX 5060 **8 GB VRAM**; **32 GB RAM**. Verificar recursos reales antes de medir.
- Morlet aceptaría dedicar hasta **500 GB de SSD** a pesos/modelos. **Espacio en disco no es memoria RAM/VRAM** y no determina tokens/s.
- El supervisor de la NPU no debería consumir la VRAM reservada a modelos grandes; **probar** que el runtime efectivamente utilice NPU.
- No ejecutar todos los modelos simultáneamente; cargar según tarea, descargar con control, medir memoria, tiempo al primer token, tokens/s y errores.
- Python **3.15.2** fue tratado como estable al 11-11-2026; compatibilidad real de drivers/runtime/paquetes puede requerir entornos separados (por ejemplo Python 3.14 para cierta versión de OpenVINO). No actualizar instalación global a ciegas.

## D. Arquitectura deseada de agentes

**Una interfaz sencilla**: abrir en el chat principal, ver estado, modelos activos, trabajo en curso y pruebas reales; evitar paneles confusos. El agente coordina de forma modular:
1. **Implementador**: modifica código exclusivamente en proyecto autorizado, bajo Git, con cambios reversibles.
2. **Verificador**: corre compilación y tests controlados; interpreta códigos de salida, no solo comentarios del LLM.
3. **Investigador**: busca alternativas para un bloqueo y propone un plan.
4. **Supervisor (NPU)**: agente especializado en clasificar y enrutar incidencias con baja latencia, dotado de sus **propios** modelos, herramientas, RAGs («racks» mencionados en voz), índices, datos y memoria.

No es obligatorio usar cuatro modelos distintos; **roles y modelos son conceptos separados**, y varios roles pueden ser tareas del mismo motor en momentos diferentes. Coordinar mediante registros y estados verificables.

## E. Supervisor (NPU): requisito literal

El usuario corrigió explícitamente «CPU o NPU» por **«NPU»**: supervisor solo en la **NPU**, sin fallback a CPU, GPU ni nube sin nueva autorización. Si el backend no puede garantizar la NPU requerida, suspender el servicio e indicar claramente **«Supervisor (NPU): no disponible»**. Registrar qué dispositivo operó realmente, no solo su etiqueta.

**Todos los nombres relacionados con ese subsistema llevan el sufijo literal `(NPU)`:** `Supervisor (NPU)`, `Modelo (NPU)`, `Herramientas (NPU)`, `RAG (NPU)`, `Memoria (NPU)`, `Estado (NPU)`, `Configuración (NPU)`.

El candidato **Qwen3-1.7B INT8** y alternativa **Qwen3-4B INT8** son ideas a **medir**, no modelos instalados. Morlet busca que el supervisor sea capaz, no tan limitado como sintió Qwen 2.5, y que responda rápidamente. Investigar otras runtimes que puedan mejorar OpenVINO **si realmente admiten NPU del 225F**. TOPS mide operaciones teóricas, **no tokens por segundo**. Ver [Supervisor (NPU)](SUPERVISOR_NPU.md).

## F. Memoria de errores / autónomo de Codex

- Por incidencia guardar en SQLite o almacenamiento equivalente: proyecto, `issue_id`, error original, hash/fingerprint, intento, diff o commit, comandos y resultados, pruebas, versión del entorno, fecha y estado.
- Consultar soluciones previamente **confirmadas**, sin filtrar secretos ni copiar información privada entre proyectos.
- **No declarar éxito** por la opinión del agente. Exigir tests significativos; si no existen, entregar estado «no verificado». Diferenciar «pasó la suite» de «producto funcional en Windows».
- Repetir pasos triviales de forma autónoma dentro de límites. **Tres fallos consecutivos** o **dos errores iguales** pueden disparar una recomendación de diagnóstico experto, **no activar directamente Astra**.
- Entregar reporte de qué cambió, qué se ejecutó, qué se comprobó, limitaciones, pendientes y reversión. No confundir reportes previos con evidencia del commit actual.
- El prototipo del laboratorio [PR #6](https://github.com/DannMorlet/Pruebas/pull/6) incluye guardado básico y CI; **no** tiene aún sandbox completo, modelo de NPU funcional, conexión al proveedor ni agente autónomo integrado.

## G. Modelos, créditos y tiempo

- Morlet valoró la experiencia de Claude Code que corre herramientas y arregla errores sin seguimiento continuo; en conversación mencionó «Fable 5.2». **Verificar el nombre exacto del modelo/proveedor** antes de configurar API.
- Para OpenAI habló de «Luna», «Sol», «Astra»; son etiquetas usadas en la conversación. La disponibilidad real, costos, selector y cuotas pueden variar. **No inventar mensajes por cinco horas**.
- Solicita que **Gemini**, referido por Morlet como «Gemini Argon 4», también pueda comprender el proyecto; se agregó guía `GEMINI.md`. La etiqueta exacta y el acceso al modelo deberán verificarse con el proveedor.
- Diseño preferido: modelo de costo reducido para tareas cotidianas; modelo potente **solo con aprobación expresa** para bloqueos, y con diagnóstico compacto para ahorrar tokens. Mostrar modelo real activo, costo conocido y resultado.
- No fingir diálogo o colaboración real entre distintos proveedores si sus conexiones no están activas.

## H. Matick Live Local (voz offline)

Morlet quiere un asistente de conversación natural parecido en utilidad a GPT Live, pero **sin afirmar que se pueda descargar GPT Live** ni que un sistema local sea idéntico.
- Requisitos: transcripción de voz offline (ASR), LLM conversacional local, síntesis en español mexicano (TTS), detección de actividad y barge-in (interrumpir).
- Candidatos discutidos: Qwen3-ASR, Qwen3.5-4B cuantizado, Piper es-MX, Silero VAD; Qwen3-TTS como opción de investigación. **Confirmar disponibilidad y licencias antes de implementar**.
- **Actualmente no tiene micrófono en su PC**, y no reportó soporte de voz funcional en Matick Studio LM. Comenzar por chat y texto→voz con bocinas; después añadir entrada de micrófono, cancelación de eco y pruebas.
- Mantener UI simple; no comprar ni instalar hardware/software sin que lo solicite. Ver [Matick Live Local](MATICK_LIVE_LOCAL.md).

## I. Reglas de seguridad

- No borrar ni modificar `C:\Windows`, TPM, Secure Boot, arranque, Defender, registro crítico, controladores, protecciones o carpetas de sistema.
- Nunca descargar/instalar/ejecutar ransomware, malware, scripts no confiables, ni desactivar antivirus. Mantener privilegios mínimos y revisar origen de dependencias.
- Instalaciones, privilegios elevados, acciones destructivas, cambios en cuentas, tokens o acceso remoto requieren permiso específico.
- Ejecutar código solo en workspace autorizado con mecanismo de aislamiento real, allowlist de operaciones y protección frente a rutas/symlinks; **una validación simple de rutas no es sandbox**.
- No subir IP privadas, tokens, claves, chats reales o archivos personales a GitHub. Documento público: registrar decisiones sin datos sensibles.
- Registrar fallos y reconocimientos de incertidumbre con honestidad; ofrecer rollback. Ver [Autonomía y seguridad](AUTONOMIA_SEGURIDAD.md).

## J. Entregables para futuros agentes bajo una petición explícita

1. Revisar qué repositorio, ramas, PRs, scripts y dependencias existen **en esa sesión**.
2. Elegir cambio concreto solicitado, no inventar tareas adicionales; registrar alcance, riesgos y criterios de aceptación.
3. Trabajar en rama/cambios reversibles, con seguridad y sin tocar proyectos ajenos.
4. Compilar/medir/probar; conservar evidencia y comunicar si no se pudo ejecutar en Windows/hardware real.
5. Distinguir: **idea**, **requisito**, **documentado**, **prototipo**, **CI verificado**, **hardware verificado** y **publicado/instalado**.
6. Al terminar: reportar evidencia, cambios, pendientes, ruta/PR real y pasos siguientes sin anunciar logros futuros como presentes.

### Glosario

- **RAG**: recuperación de conocimientos/documentos (índices, embeddings, búsquedas) para el agente.
- **«Racks»**: palabra mencionada por Morlet en voz. Registrar la intención de mantener el conjunto de recursos de la NPU separado; antes de crear una categoría nueva de «racks», precisar si significa RAGs, conectores o almacenamiento.
- **NPU vs CPU vs GPU**: chips distintos. El «Supervisor (NPU)» es un requisito de ubicación física de ejecución, no solo etiqueta de interfaz.
- **TOPS vs tokens/s**: medidas distintas; no inferir tokens/s mediante multiplicar o dividir 13 TOPS sin benchmark.
- **Matick Studio LM vs LM Studio**: aplicación propia frente a motor/servidor externo que puede integrarse.

**Fuente de especificación:** acuerdos hablados con Morlet durante la sesión del 11-11-2026, materializados para que los agentes futuros lean y trabajen **solo cuando Morlet lo ordene**.
