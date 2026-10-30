# Prueba de Skill Alexa en desarrollo — es-MX

## Antes de cambiar la Skill actual

1. Abre la Skill ID `amzn1.ask.skill.8a0bdb03-ba75-4bf3-b205-f62f4ded3499` en la cuenta de desarrollador propietaria.
2. Antes de editar, copia el modelo `es-MX` y el código desplegado. Esa copia sirve para restaurar las rutas funcionales.
3. Revisa el nombre de invocación activo y conserva los intents, slots, frases y handlers que ya funcionen. El JSON del repositorio es una propuesta candidata; no reemplaces el modelo completo con ese archivo.
4. Si pruebas `matick inteligente`, cambia solo el nombre de invocación y conserva el resto del modelo. Compila `es-MX`; si falla la compilación o el Echo deja de abrirla, restaura la copia previa.
5. En **Code**, compara el handler desplegado con `alexa/lambda/` e integra solo lo necesario. No reemplaces todo el `index.js` antes de preservar sus handlers existentes. Configura `MATICK_BRIDGE_TOKEN` como secreto; no lo guardes en código ni archivos versionados.
6. En **Test**, selecciona **Development** y `es-MX`; confirma que el test esté habilitado.
7. Guarda nombre visible, descripción e iconos de `FICHA_ES_MX.md` en **Distribution/Store Preview**. Los iconos están en `assets/`.

## App Alexa y Echo Dot 5

1. Usa en la app Alexa la misma cuenta Amazon que es propietaria o tester autorizado de la Skill.
2. Confirma que el Echo Dot 5 está registrado en esa cuenta y con idioma/región **Español (México)**.
3. En la app Alexa, busca la Skill de desarrollo en **Más > Skills y juegos > Tus Skills > Dev** y habilítala si aparece. Si no aparece, revisa cuenta, locale y estado de prueba en Console.
4. Di el nombre que aparece guardado en **Build > Invocation**. Usa «Alexa, abre Matick Inteligente» solo si ese candidato ya se guardó y compiló.
5. Di: «pregunta qué es una red neuronal». Debe responder una consulta real del Worker.
6. Di: «ayúdame a corregir el código de mi proyecto». Debe contestar y sugerir ChatGPT Work/Codex. Revisa la tarjeta en la app Alexa.
7. Prueba una pregunta sin conexión y confirma que el mensaje no exponga tokens o detalles internos.

## Criterio para dar por resuelto

La prueba del simulador y la respuesta de `/health` solo verifican partes aisladas. Marca como **prueba física aprobada** únicamente después de invocar y preguntar desde el Echo Dot 5 real, con el endpoint `/chat` configurado y la misma cuenta/región de desarrollo. Anota fecha, región, resultado de invocación y resultado de pregunta.
