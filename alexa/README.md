# Matick Inteligente — adaptador existente recuperado

Origen: rama `codex/matick-director-routing-v0.2.0`, commit `aa452c9` de DannMorlet/IA-Local-Cursor. Se incorporó únicamente alexa/, sin sustituir Windows ni el servidor cloud. No es una nueva Skill ni un nuevo Worker. ID existente: `amzn1.ask.skill.8a0bdb03-ba75-4bf3-b205-f62f4ded3499`.

El modelo recuperado decía `matic set`; esta revisión prepara `matick inteligente` conforme a la frase solicitada. Es un cambio local pendiente de guardar y compilar en la consola. No demuestra cuál de los dos nombres está desplegado.

`lambda/` es el adaptador modular con pruebas. `MatickInteligente_index.js` es la variante autónoma previamente existente para integración manual. Comparar primero con el código activo y conservar handlers propios, incluidos Matick Home; no desplegar ambas variantes ni reemplazar código activo sin copia de respaldo.

Contrato conservado: POST al Worker existente `/chat`, autorización Bearer mediante configuración privada existente, cuerpo `{pregunta, historial}`, respuesta `{ok:true, respuesta}`. No confundirlo con el servidor Python de cloud/, que es otro componente. No se recuperó la fuente del Worker; no se creó otro ni se alteró su configuración. El historial corto viaja por sesión; confirmar privacidad y retención del Worker antes de certificar.

Pruebas locales: `cd alexa/lambda`, `npm ci --ignore-scripts`, `npm test`. Usan HTTP localhost simulado; no consumen IA ni prueban el Echo. La CI añadida ejecutará estas pruebas cuando se publique el cambio en GitHub.

Para la consola y el Echo: seguir PRUEBA_ECHO.md y ../docs/MATICK_INTELIGENTE_ALEXA.md. Integrar únicamente los cambios necesarios. Conservar los secretos actuales; no copiar config.private.json a GitHub.

Estado: reconocimiento físico pendiente; generación IA real pendiente; beta no activada; certificación no enviada; publicación no realizada.
