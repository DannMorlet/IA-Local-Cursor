# Matick Inteligente: diagnóstico y verificación pendiente

Fecha: 2026-10-30, America/Mexico_City.

Skill declarada: `amzn1.ask.skill.8a0bdb03-ba75-4bf3-b205-f62f4ded3499`.
Backend declarado: Alexa-hosted Node.js, ask-sdk-core. Worker declarado:
`https://matick-alexa-cloud.danymorlet98.workers.dev`.

## Actualización tras buscar las ramas remotas

Se encontró alexa/ en `codex/matick-director-routing-v0.2.0`, commit `aa452c9`. Se recuperó sólo esa carpeta en el checkout existente, conservando sus variantes modular y autónoma. El modelo recuperado usaba `matic set`: se preparó `matick inteligente` conforme a la solicitud actual. El nombre realmente desplegado sigue pendiente de verificar. Se corrigió el manejo de JSON null en ambas variantes; el endpoint y contrato /chat permanecen. Once pruebas Node pasan con transporte simulado y SDK real para saludo/pregunta. No prueban reconocimiento físico ni inferencia real. Esta actualización resuelve la ausencia local del adaptador descrita en la evidencia inicial; no se encontró la fuente del Worker.

## Evidencia inicial y límites

- El usuario informa que /health respondió y que el simulador abre la Skill. No son verificaciones independientes de esta sesión.
- Checkout inspeccionado: DannMorlet/IA-Local-Cursor, rama work, HEAD 8800b55. Estado inicial limpio. No contiene código Alexa-hosted, modelo es-MX, manifiesto ASK ni fuentes del Worker. El README describe otro MVP, sin integración real de IA. No permite inferir el estado del despliegue existente.
- Búsqueda conectada de matick-alexa-cloud: sin resultados. El acceso conectado puede ser incompleto.
- La consulta web oficial devolvió error, tanto en búsqueda como al abrir páginas. No se verificó su contenido vigente.
- La política de red del entorno está restringida y no incluye Amazon ni el Worker. No se probaron esos servicios ni se intentó eludir esa política.
- Pruebas del MVP disponible: desde cloud, `python -m unittest discover -s tests -v`: 4 aprobadas. Una primera ejecución desde la raíz falló por ruta de importación; no fue un defecto del backend Alexa.
- Reconocimiento en Echo: pendiente. Generación IA en Echo: pendiente. Beta, certificación y publicación: no realizadas.

## Diagnóstico diferencial

Que el simulador funcione confirma únicamente ese recorrido de prueba. No confirma la cuenta del Echo, el locale del dispositivo, la habilitación de la Skill, la transcripción de la voz ni una llamada a IA. La ausencia de publicación explica que no aparezca como Skill pública; por sí sola no impide usar una versión de desarrollo en la cuenta autorizada.

Comprobar primero cuenta Amazon del dispositivo frente a la cuenta de desarrollo, habilitación del testing, locale es-MX y nombre de invocación desplegado. Después revisar disponibilidad por marketplace y aceptación de beta si se usa otra cuenta. Alexa Household y perfiles de voz no sustituyen el registro del dispositivo en la cuenta adecuada.

## Pasos manuales en Amazon Developer Console

Estas son instrucciones de preparación, no acciones realizadas. Los nombres de menús pueden variar; contrastar con la ayuda oficial vigente.

1. Abrir Alexa Developer Console y seleccionar por ID la Skill existente. Conservar su backend Alexa-hosted.
2. Build: seleccionar Español (MX), revisar que Invocation Name sea `matick inteligente`. El título comercial no determina la invocación. Guardar y compilar el modelo si hay cambios; esperar éxito. No renombrar por ensayo sin revisar primero la transcripción del Echo.
3. Code: comprobar que la versión correcta ya está desplegada. No reemplazar el endpoint Alexa-hosted por /health del Worker. /health es diagnóstico, no un manejador de solicitudes Alexa.
4. Test: habilitar pruebas en Development. Seleccionar es-MX en el simulador. Probar apertura y una pregunta por separado; conservar requestId y tipo de solicitud, sin tokens ni texto privado.
5. En Alexa móvil, comprobar la cuenta iniciada y en el Echo comprobar la cuenta de registro. Deben corresponder a la cuenta autorizada de desarrollo o a un tester que aceptó la beta. No desregistrar ni cambiar de país como primer intento.
6. En Dispositivos > Echo y Alexa > Echo Dot > configuración > Idioma, comprobar Español (México). En la configuración de cuenta de Amazon comprobar país/región y marketplace; no confundirlo con la región de alojamiento Lambda ni con la zona horaria. Revisar México en la disponibilidad de distribución. No migrar la cuenta sin evaluar las consecuencias.
7. En Skills y juegos > Tus Skills, buscar la sección de desarrollo (Dev) y confirmar habilitación cuando aparezca. No esperar encontrar una Skill inédita en el catálogo público.
8. Decir `Alexa, abre Matick Inteligente`. Consultar el historial de voz/actividad y comprobar qué entendió Alexa. Si no hay LaunchRequest en los logs del backend, investigar reconocimiento y acceso antes del Worker.

## Beta para Echo Dot 5

No es obligatoria para probar con la propia cuenta desarrolladora. Para una cuenta distinta, usar la beta oficial, sin publicar aún.

1. En Distribution > Availability, localizar Beta Test / Beta Testing si está disponible para esta Skill. Completar los campos requeridos por la consola y registrar únicamente el correo de la cuenta Amazon usada por el Echo.
2. Añadir al tester y comenzar la beta siguiendo la consola. No enviar invitaciones a terceros sin autorización.
3. Desde la cuenta Amazon correcta, abrir la invitación, aceptar y habilitar la Skill. Una invitación enviada no prueba aceptación ni habilitación.
4. Comprobar que el tester aparece aceptado/habilitado y repetir las dos pruebas físicas. Si no aparece Beta Testing, verificar elegibilidad y documentación actual; no crear otra Skill.
5. Confirmar en la documentación vigente los límites de testers, duración y renovación; no asumir que la beta es distribución permanente.

## Preparación para México y certificación

- Distribución pública con México incluido y locale es-MX compilado. Nombre, descripción y ejemplos deben coincidir con funciones probadas.
- Completar iconos requeridos, categoría, contacto, instrucciones de uso, privacidad y cumplimiento. Proporcionar una política de privacidad real, accesible y coherente con el tratamiento de preguntas por Matick Cloud y el proveedor de IA. No inventar URLs ni afirmar que se almacenan o borran datos sin comprobarlo.
- Revisar requisitos vigentes de Amazon para contenido generado por IA, contenido restringido, menores y tratamiento de datos. No presentar ChatGPT/OpenAI como una integración oficial o patrocinio sin fundamento.
- Validar Launch, Help, Stop, Cancel, Fallback, entrada vacía, error de red, límite de tiempo y SSML seguro. Escapar contenido dinámico al emitir SSML; comprobar el código existente antes de aplicar un parche.
- Revisar que el slot y el intent actuales realmente capturan preguntas en es-MX. No asumir que una configuración de búsqueda libre de otro locale es compatible.
- Confirmar que las respuestas llegan dentro del plazo Alexa aplicable y que los errores dejan una respuesta útil. Medir el recorrido completo; /health no mide inferencia.
- Mantener el contrato actual Alexa → Matick Cloud → IA y las credenciales existentes. No introducir otra clave en código, modelo de interacción o documentación.
- Conservar handlers y contratos futuros de Matick Home. Describirlos como futuros si no están operativos; no anunciarlos como disponibles en la ficha.
- Ejecutar validaciones de la consola y pruebas funcionales; completar instrucciones claras para el certificador con frases reales del modelo y sin credenciales privadas. Sólo enviar a certificación después de resolver fallos; envío, aprobación y publicación son estados distintos.

## Dos puertas de aceptación independientes

| Prueba | Procedimiento | Evidencia requerida |
| --- | --- | --- |
| Reconocimiento | Echo físico: abrir la Skill con la frase objetivo | Transcripción correcta, LaunchRequest del ID esperado y saludo real oído |
| IA | Dentro de esa sesión, usar una frase soportada con una pregunta nueva | Intent/slot recibido, llamada correlacionada al Worker y al proveedor con éxito, respuesta IA oída; distinguir errores y respuestas prefijadas |

Registrar fecha, locale, dispositivo, estado de acceso, requestId y latencia; no registrar claves, cabeceras de autorización ni conversaciones completas. Un saludo exitoso no prueba IA. Una respuesta HTTP 200 o /health tampoco prueba IA. Para confirmar generación, revisar el resultado real del proveedor y distinguir un fallback estático.

## Referencias oficiales para contrastar

- Pruebas: https://developer.amazon.com/en-US/docs/alexa/devconsole/test-your-skill.html
- Beta: https://developer.amazon.com/en-US/docs/alexa/custom-skills/skills-beta-testing.html
- Invocación: https://developer.amazon.com/en-US/docs/alexa/custom-skills/choose-the-invocation-name-for-a-custom-skill.html
- Certificación: https://developer.amazon.com/en-US/docs/alexa/custom-skills/certification-requirements-for-custom-skills.html

Son referencias de consulta; no se pudo comprobar su contenido o vigencia en esta sesión.
