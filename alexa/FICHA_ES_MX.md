# Matick Inteligente — ficha de Alexa (es-MX)

Valores preparados para copiar a Alexa Developer Console. La ficha no queda publicada en la cuenta hasta guardar los cambios en la consola.

| Campo | Valor |
| --- | --- |
| Nombre de la Skill | Matick Inteligente |
| Nombre de invocación (frase hablada) | matic set |
| Idioma | Español (México) — es-MX |
| Frase de apertura | «Alexa, abre Matic Set» |
| Descripción breve | Pregunta a ChatGPT en español y recibe una sugerencia para continuar tareas técnicas en ChatGPT Work o Codex. |
| Categoría sugerida | Educación / Referencia (selecciona la categoría disponible más cercana en Console) |
| País de distribución | México |

## Descripción larga

Matick Inteligente responde preguntas en español mediante ChatGPT conectado a un servicio seguro en la nube. Pregunta sobre un tema, pide una explicación o solicita ayuda para entender un problema.

Cuando una solicitud requiere revisar o cambiar archivos, programar, ejecutar código o trabajar con un repositorio, Matick puede recomendarte continuar en ChatGPT Work o Codex y mostrar un resumen en la tarjeta de la aplicación Alexa. Alexa no abre esas aplicaciones ni transfiere o ejecuta la tarea automáticamente.

Las respuestas dependen de la conexión con el servicio en la nube. No compartas contraseñas, claves ni información sensible por voz.

## Frases de ejemplo

- Alexa, pregunta a Matick Inteligente qué es una red neuronal.
- Alexa, pide a Matick Inteligente que me explique este error.
- Alexa, dile a Matick Inteligente que me ayude a reparar mi Skill.
- Alexa, pregunta a Matick Inteligente cómo funciona Cloudflare.
- Alexa, pide a Matick Inteligente una idea para organizar mi proyecto.

## Ayuda y privacidad

La Skill envía la pregunta y un historial corto de la sesión al Cloudflare Worker configurado para generar una respuesta con ChatGPT. No se debe certificar hasta que la política de privacidad, el contacto del desarrollador, la retención real de datos y los permisos declarados coincidan con la implementación desplegada.

Falta completar en Console el correo de contacto, la URL pública de política de privacidad y los detalles de tratamiento de datos. No usar enlaces ficticios ni declarar que no se recopilan datos si el Worker conserva registros.

## Icono

Carga `assets/matick-inteligente-icon-512.png` como icono grande y `assets/matick-inteligente-icon-108.png` como icono pequeño si Console muestra ambos campos. El PNG maestro está en `assets/matick-inteligente-icon.png`.
