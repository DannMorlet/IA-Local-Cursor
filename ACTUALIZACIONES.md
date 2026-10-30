# Actualizaciones

## 2026-10-30 — Matick Inteligente, diagnóstico Alexa

Solicitud: continuar la Skill existente sin reemplazar componentes. Checkout cloud inspeccionado en HEAD 8800b55; no contiene el backend Alexa-hosted ni el Worker descritos. Se añadió docs/MATICK_INTELIGENTE_ALEXA.md con diagnóstico diferencial, instrucciones manuales de desarrollo/beta/certificación y dos pruebas de aceptación independientes. No se modificaron código de producción, endpoints, credenciales ni configuraciones existentes.

Pruebas: 4 tests del MVP Python aprobados al ejecutar desde cloud. Primera ejecución desde raíz falló por ruta de importación. Estas pruebas no verifican Alexa ni IA. Consulta web fallida; red restringida sin Amazon/Worker habilitados. No hubo activación beta, certificación, publicación ni prueba física.

Pendiente: identificar repositorio/rama reales de Alexa y Worker, inspeccionar su código, verificar cuenta/locale/testing en consola y realizar pruebas separadas de reconocimiento y generación IA en Echo. Este registro pertenece al checkout de nube; no se actualizó ni sincronizó C:\IA\Matick Studio LM.


## 2026-10-30 — Recuperación del adaptador Alexa existente

Autorización: buscar en GitHub y, si hace falta, incorporar a IA-Local-Cursor. Se enumeraron los cuatro repositorios accesibles y las ramas de IA-Local-Cursor; apareció alexa/ en codex/matick-director-routing-v0.2.0, aa452c9. Esto resuelve el pendiente de localizar el adaptador, sin recrearlo. Se recuperó exclusivamente alexa/, conservando el resto del checkout y sus cambios. No se encontró la fuente del Worker.

Hallazgo: el modelo recuperado invocaba matic set. Se preparó matick inteligente, alineando modelo, prueba, ficha y guía. No se afirma que esa discrepancia exista en el modelo desplegado. Contrato, endpoint, secretos y enrutamiento conservados. Se corrigió JSON null que podía lanzar una excepción asíncrona sin manejar; regresión cubierta en localhost. Se agregó lockfile y trabajo CI para Alexa.

Validación: 11 pruebas Node aprobadas, incluyendo saludo con SDK, pregunta y escape SSML con transporte simulado, contrato /chat en localhost y error null. La primera prueba del SDK usó incorrectamente su interfaz como Promise; se corrigió el arnés a callback y pasó. No es un fallo observado en Alexa-hosted. No hubo llamadas de IA reales ni consumo del proveedor. git diff --check sin errores. Pendientes independientes: modelo/cuenta/locale en consola, reconocimiento Echo y respuesta IA real. Beta/certificación/publicación no realizadas. Cambios sólo en nube y GitHub, sin sincronización al Windows local.
