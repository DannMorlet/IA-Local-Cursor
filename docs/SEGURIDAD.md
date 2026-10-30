# Seguridad de Matick Studio LM

Esta base es un **MVP** y no se debe exponer directamente a internet sin medidas adicionales.

1. En la nube, servir exclusivamente detrás de un reverse proxy **HTTPS** (TLS). El servidor de ejemplo utiliza HTTP dentro de una red confiable; `http://127.0.0.1` es adecuado solo para pruebas locales.
2. Crear tokens aleatorios, únicos y largos para cada rol en `MATICK_TOKENS_JSON`. No guardarlos en Git, logs, Issues ni `.env` versionado. Rotarlos ante sospechas de filtración.
3. Nunca usar la misma clave para todos los clientes. No distribuir secretos de servicios privilegiados dentro de un `.exe` público: se extraen del binario. La integración final debe usar autorización delegada y credenciales de alcance limitado.
4. Ejecutar procesos con el menor privilegio posible. El servicio actual **no tiene endpoints de ejecución de comandos, captura de pantalla ni control del teclado**. Mantenerlos fuera hasta implementar autorizaciones explícitas, registros y un botón de parada.
5. Datos de reloj, salud o audio pueden ser sensibles. No enviarlos sin consentimiento explícito; crear políticas de retención, cifrado y borrado antes de implementarlos.
6. Añadir rate limits, cuota por identidad, métricas, alertas, rotación de claves, backups, protección CSRF para futuras interfaces web y firewall del host antes de ofrecer servicio público.
7. Evitar confiar en cadenas `source` suministradas por clientes. La implementación actual deriva el emisor de su token. En producción usar identidad autenticada con scopes.
8. SQLite es un almacén local para un proceso. Para varias réplicas se requiere un backend central, migraciones y semántica explícita de confirmaciones.
9. La matriz del MVP deja a `matick-studio-lm` y `chatgpt` dirigir eventos a roles permitidos; los demás roles solo escriben a esos dos directores. `matick-pet` es un receptor de solo lectura. Mantener la matriz explícita al añadir componentes.
10. `status.snapshot` solo lo publica `matick-studio-lm` y se puede entregar a `matick-pet`. El adaptador de la mascota aún no existe. Publicar únicamente estado de tarea/servicio; excluir pasos, pulso, sueño, credenciales, transcripciones y datos personales.
11. El rol `alexa` del transporte no verifica por sí mismo las firmas de solicitudes de Alexa. El adaptador Alexa debe validar la solicitud de Skills Kit antes de emitir eventos con su token.

## Privacidad

La ruta `/health` no debe exponer nombres de usuario ni tokens. `/v1/events` filtra mensajes según el rol autenticado; **esto no es aislamiento entre usuarios finales**, solo entre componentes. No alojar información real de varios usuarios sin introducir separación estricta por cuenta.

## Publicar en GitHub ≠ desplegar a la nube

Un repositorio público permite revisar el código, no ejecuta un servidor 24/7. Los binarios de GitHub Actions se generan solo al disparar workflows y un resultado verde no implica que el servicio esté desplegado.

