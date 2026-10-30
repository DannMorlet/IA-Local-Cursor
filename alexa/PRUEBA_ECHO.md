# Prueba de Skill Alexa en desarrollo — es-MX

## Primero en Developer Console

1. Abre la Skill ID `amzn1.ask.skill.8a0bdb03-ba75-4bf3-b205-f62f4ded3499` en la cuenta de desarrollador propietaria.
2. En **Build > Invocation**, configura `matic set` y guarda el modelo `es-MX` de `interactionModels/custom/es-MX.json`.
3. En **Build > Interaction Model**, compila el modelo para es-MX y confirma que la compilación termine correctamente.
4. En **Code**, instala dependencias de `alexa/lambda/package.json`, actualiza el manejador con estos archivos y carga `MATICK_BRIDGE_TOKEN` como variable segura o secreto del backend. No pegues el token en el código ni en archivos versionados.
5. En **Test**, cambia el estado a **Development** y selecciona `es-MX`. La consola debe mostrar que la prueba está habilitada.
6. Guarda el nombre, descripción, iconos y ejemplos de `FICHA_ES_MX.md` en **Distribution/Store Preview**. Los iconos generados están en `assets/`.

## App Alexa y Echo Dot 5

1. Usa en la app Alexa la misma cuenta Amazon que es propietaria o tester autorizado de la Skill.
2. Confirma que el Echo Dot 5 está registrado en esa cuenta y con idioma/región **Español (México)**.
3. En la app Alexa, busca la Skill de desarrollo en **Más > Skills y juegos > Tus Skills > Dev** (la ubicación y etiqueta pueden variar por versión) y habilítala si aparece. Si no aparece, revisa cuenta, locale y el estado **Development** en Console.
4. Di: «Alexa, abre Matic Set». Debe escuchar el saludo de lanzamiento. Esta frase aún requiere confirmación de reconocimiento en el Echo real.
5. Di: «pregunta qué es una red neuronal». Debe responder una consulta real del Worker.
6. Di: «ayúdame a corregir el código de mi proyecto». Debe contestar y sugerir ChatGPT Work/Codex. Revisa la tarjeta en la app Alexa.
7. Prueba una pregunta sin conexión y confirma que el mensaje no exponga tokens o detalles internos.

## Criterio para dar por resuelto

La prueba del simulador y la respuesta de `/health` solo verifican partes aisladas. Marca como **prueba física aprobada** únicamente después de invocar y preguntar desde el Echo Dot 5 real, con el endpoint `/chat` configurado y la misma cuenta/región de desarrollo. Anota fecha, región, resultado de invocación y resultado de pregunta.
