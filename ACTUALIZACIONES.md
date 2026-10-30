# Actualizaciones Matick Studio LM

## 30 de octubre de 2026 — Dirección de componentes v0.2.0

- **Solicitud:** preparar Matick Studio LM para dirigir eventos entre los componentes del ecosistema.
- **Causa:** la API aceptaba eventos entre roles, pero no tenía matriz de rutas, envío explícito a varios destinatarios ni rol de estado para la mascota. La app Windows solo verificaba `/health`.
- **Cambios:** añadidos `POST /v1/direct`, `GET /v1/routes`, permisos de destino por rol y el rol de solo lectura `matick-pet`. `status.snapshot` solo puede salir de `matick-studio-lm`; acepta un esquema operativo reducido y la mascota solo recibe ese tipo. El cliente de prueba permite consultar rutas y enviar eventos dirigidos. README y documentos describen qué ya hace el bus y qué conectores siguen pendientes. Versión cloud `0.2.0`.
- **Seguridad:** el token determina el emisor; el fan-out exige destinos explícitos; no se admiten comodines. Los adaptadores deben validar sus propias identidades. Alexa debe validar las firmas de Skills Kit; esa validación no se agrega por el rol del bus.
- **Pruebas:** seis pruebas unitarias locales aprobadas; `compileall` aprobado; ayuda CLI `direct` y `routes` revisada. La compilación DirectX 12 requiere CI Windows y aún no se ha verificado en esta ejecución.
- **Estado real:** el bus puede dirigir eventos cuando los componentes se conecten. Los adaptadores de Alexa, ChatGPT, Matick Chat, Matick Codex, Matick Reloj y Matick Pet todavía no están conectados; el ejecutable Windows sigue consultando `/health`.
- **Pendientes:** integrar cada cliente y probarlo en su entorno real; añadir la conexión segura de la app Windows al director; convertir snapshots operativos en una actualización compatible con la mascota Work; ejecutar CI Windows; resolver por separado la activación/publicación de la Skill Alexa y probarla en Echo Dot 5.
