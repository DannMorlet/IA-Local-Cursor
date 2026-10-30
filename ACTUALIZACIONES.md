# Actualizaciones Matick Studio LM

## 30 de octubre de 2026 — Alexa y ficha de Matick Inteligente

- **Solicitud:** actualizar la Skill para español de México, preparar un icono identificable y dejar instrucciones de uso en Development con Echo Dot 5, manteniendo las entradas funcionales existentes.
- **Cambios:** añadido un handler Alexa Skills Kit que enruta preguntas al Cloudflare Worker, modelo `es-MX` con `PreguntaIntent`/slot `consulta`, recomendación clara de ChatGPT Work/Codex para tareas exigentes, ficha en español, dos tamaños de icono, pruebas automatizadas y guía de Console/Echo. Nombre visible: Matick Inteligente. Frase hablada acordada: `matic set` («Alexa, abre Matic Set»).
- **Privacidad:** token leído desde secreto o archivo privado ignorado; no se guardan preguntas en logs; la tarjeta puede contener un resumen de la consulta. Revisar los registros y la retención reales del Worker antes de certificar.
- **Pruebas locales:** siete pruebas aprobadas, incluida frase de invocación y esquema de `PreguntaIntent`/`consulta`; también cubren sugerencia de Work, limpieza de salida/SSML, HTTPS/token, límite de historial y contrato HTTP de `/chat` simulado en localhost. También pasan la sintaxis Node y la validación JSON del modelo. Esto no prueba el Worker productivo ni un Echo.
- **Estado de integración:** `/health` funciona, pero `/chat` respondió “Servicio pendiente de configuración”. Amazon Console responde “We do not support your session or client”; no pudimos leer o guardar el modelo/código activo. Por tanto, no se reemplazó ninguna entrada de la Skill de Amazon. El modelo y handler del repositorio son candidatos y se deben fusionar con el original después de preservarlo.
- **Prueba real:** Echo Dot 5 no disponible a esta ejecución; ninguna prueba física se declara aprobada.
- **Pendiente:** configurar token secreto compatible en Alexa-hosted, validar en simulator, habilitar Test: Development para `es-MX`, asociar dispositivo/cuenta y validar invocación y pregunta real en Echo; completar contacto y política de privacidad antes de enviar a certificación.
- **Límites de presupuesto:** Alexa no recibe el porcentaje restante de Codex, por lo que no puede avisar automáticamente cada 10% ni pausar al llegar a 10% disponible. El enrutamiento recomienda ChatGPT primero y sugiere Work/Codex para tareas exigentes. La llamada del Worker es una integración de API independiente de la sesión visible ChatGPT; confirma su esquema de facturación en Cloudflare/OpenAI antes de habilitarla.

## 30 de octubre de 2026 — Dirección de componentes v0.2.0

- **Solicitud:** preparar Matick Studio LM para dirigir eventos entre los componentes del ecosistema.
- **Causa:** la API aceptaba eventos entre roles, pero no tenía matriz de rutas, envío explícito a varios destinatarios ni rol de estado para la mascota. La app Windows solo verificaba `/health`.
- **Cambios:** añadidos `POST /v1/direct`, `GET /v1/routes`, permisos de destino por rol y el rol de solo lectura `matick-pet`. `status.snapshot` solo puede salir de `matick-studio-lm`; acepta un esquema operativo reducido y la mascota solo recibe ese tipo. El cliente de prueba permite consultar rutas y enviar eventos dirigidos. README y documentos describen qué ya hace el bus y qué conectores siguen pendientes. Versión cloud `0.2.0`.
- **Seguridad:** el token determina el emisor; el fan-out exige destinos explícitos; no se admiten comodines. Los adaptadores deben validar sus propias identidades. Alexa debe validar las firmas de Skills Kit; esa validación no se agrega por el rol del bus.
- **Pruebas:** seis pruebas unitarias locales aprobadas; `compileall` aprobado; ayuda CLI `direct` y `routes` revisada. La compilación DirectX 12 requiere CI Windows y aún no se ha verificado en esta ejecución.
- **Estado real:** el bus puede dirigir eventos cuando los componentes se conecten. Los adaptadores de Alexa, ChatGPT, Matick Chat, Matick Codex, Matick Reloj y Matick Pet todavía no están conectados; el ejecutable Windows sigue consultando `/health`.
- **Pendientes:** integrar cada cliente y probarlo en su entorno real; añadir la conexión segura de la app Windows al director; convertir snapshots operativos en una actualización compatible con la mascota Work; ejecutar CI Windows; resolver por separado la activación/publicación de la Skill Alexa y probarla en Echo Dot 5.
