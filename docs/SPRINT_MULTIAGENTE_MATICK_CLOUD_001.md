# Matick Studio LM Cloud — Sprint multiagente 001

**Fecha:** 2026-10-31 (America/Mexico_City)  
**Estado:** tareas asignadas; entregables de Gemini y Claude pendientes.  
**Proyecto existente:** [DannMorlet/IA-Local-Cursor](https://github.com/DannMorlet/IA-Local-Cursor)  
**Rama de trabajo:** `feature/matick-cloud-health-cli-gemini-20261031`  
**PR de prueba:** [#8](https://github.com/DannMorlet/IA-Local-Cursor/pull/8) (**borrador**, sin fusionar).  
**Chat central del equipo:** [CHATS_Gemini_GPT.md](https://docs.google.com/document/d/18LMpu2VgfBSaYjX06-JtGcAwhYxdLxr8lEOFluWyQPE/edit), anuncio `TEAM-0014`.

## Objetivo

Una iteración de Matick Studio LM Cloud que ofrezca un estado de conexión comprensible y verificable, sin fingir modelos o conectores operativos y sin encarecer el producto. Arquitectura Windows nativa C++ / Direct3D 12, servidor HTTP Python con SQLite. Es un producto **independiente de LM Studio**.

El proyecto mantiene la interfaz y mascota originales como dirección visual: la mascota actual es provisional. No sustituir por Electron o un frontend web sin decisión de Morlet.

## Situación de partida comprobada

- La rama de prueba contiene el comando `python -m matick_cloud.client health`, sin token.
- El cliente Windows comprueba `/health` y luego `/v1/status` para verificar sesión; F5 solicita un nuevo sondeo.
- Los estados de la API se diferencian en `Conectado` (API autenticada), `SinSesion`, `Desconectado` y `NoConfigurado`.
- [GitHub Actions run 41227705394](https://github.com/DannMorlet/IA-Local-Cursor/actions/runs/41227705394) finalizó correctamente (pruebas cloud y compilación Windows DirectX 12 x64). **No prueba el aspecto final de la aplicación en el PC**.
- Sin despliegue permanente, sin inferencia cloud y sin integraciones verificadas de Alexa, Gemini, Claude, ChatGPT, reloj o modelo.
- `main` permanece sin modificaciones de este sprint.

## Agente Gemini — diseño y accesibilidad

**Entrada:** `docs/UI_REFERENCIA_MATICK.md`, `windows/src/dashboard.cpp`, `windows/src/main.cpp` y el PR #8.

**Entrega en Google Drive:** nuevo `TEAM` dirigido al sprint, describiendo:
1. Distribución concreta de los cuatro estados, junto a la mascota, sin mostrar otros conectores como conectados.
2. Microtexto exacto para servidor activo sin sesión, servicio no disponible, falta de configuración y API autenticada.
3. Comportamiento con F5, errores de red y reducción de movimiento. Considerar accesibilidad y tamaño de ventana actual.
4. Cuatro pruebas de aceptación visibles que puedan comprobarse en Windows 11.
5. Alternativa mínima de bajo coste y mejoras futuras opcionales, separando claramente lo no implementado.

**No afirmar que el diseño ya es código.**

## Agente Claude — QA, seguridad y coste

**Entrada:** `cloud/matick_cloud/client.py`, `cloud/matick_cloud/server.py`, `windows/src/main.cpp`, `docs/SEGURIDAD.md`, el PR #8 y sus pruebas.

**Entrega en Google Drive:** nuevo `TEAM` con:
1. Revisión P0/P1/P2 de fallos **reproducibles**, con ruta y función; diferenciar vulnerabilidad comprobada de riesgo hipotético.
2. Investigar el transporte de los tokens del cliente Python hacia destinos remotos: el código observado construye `Authorization: Bearer` pero no exige explícitamente HTTPS para un `MATICK_CLOUD_URL` remoto. Comparar con la comprobación realizada por el cliente DX12. Proponer cambio y pruebas; no exponer tokens reales.
3. Revisar política ante redirecciones HTTP de peticiones autenticadas, cierre de hilos/ventanas, reintentos y errores de WinHTTP.
4. Proponer 4 pruebas de regresión automatizadas y 3 pruebas manuales de interfaz.
5. Comparar ejecución local sin cuota cloud vs. despliegue remoto opcional (TLS, dominio, mantenimiento, backups); no inventar tarifas actuales.

**Nota de trabajo:** ChatGPT identificó el riesgo del transporte del token y quiso actualizar el archivo de cliente, pero la herramienta rechazó la operación. **No está corregido en código.** No declarar mitigación implementada hasta que un commit y CI la comprueben.

## Agente ChatGPT — integración y ejecución

1. Analizar propuestas de Gemini y Claude solo cuando aparezcan realmente en Drive; consolidar contradicciones y documentar supuestos.
2. Implementar parches pequeños en una rama y mantener el PR de borrador; no fusionar ni desplegar automáticamente.
3. Ejecutar/revisar pruebas Python y compilación DX12; distinguir CI de pruebas visuales físicas.
4. Comunicar avances en `CHATS_Gemini_GPT.md` y dejar relación de commits, riesgos y pruebas.
5. Evitar exposición de secretos, fabricación de métricas de GPU/CPU/NPU y cambios sin autorización.

## Coordinación y criterios de aceptación

- El canal Google Drive conserva mensajes con IDs únicos, autor, respuesta_a y estado.
- Gemini y Claude deben iniciar sus propias sesiones o tener una automatización autorizada; **editar Drive no activa sus modelos automáticamente**.
- Cada mensaje debe poder verificarse como guardado; una firma textual por sí sola no prueba qué modelo lo escribió.
- No exponer credenciales, datos personales, IP privadas ni otros secretos.
- Éxito del sprint técnico: pruebas automatizadas completas, una propuesta implementable de UX, auditoría QA priorizada, decisiones anotadas y PR reproducible; la UI real debe verificarse también en Windows.
- Entregas de Gemini/Claude pendientes al crear este archivo. El trabajo de `Mi Moto` queda pausado, no borrado.
