# Prueba de colaboración: Matick Studio LM Cloud × Gemini + ChatGPT

**Fecha de inicio:** 2026-10-31 (America/Mexico_City)  
**Repositorio:** `DannMorlet/IA-Local-Cursor`  
**Proyecto:** Matick Studio LM Cloud (no confundir con la instalación local de Matick Studio LM)  
**Alcance:** un primer incremento pequeño, sin gasto ni despliegue público.

## Objetivo comprobable

Construir gradualmente un **panel de estado real** para Matick Studio LM Cloud que distinga entre servidor HTTP disponible, identidad autenticada, mensajería funcional e integraciones pendientes. No mostrar conexiones ficticias.

## Dos agentes y un canal

- **Gemini — arquitecta creativa:** definir UX/flujo del panel, jerarquía visual, estados, microcopys, alternativa mínima y ampliación futura. Debe leer la especificación existente `docs/UI_REFERENCIA_MATICK.md` antes de proponer cambios.
- **ChatGPT — ingeniero integrador:** verificar el código, implementar mejoras compatibles, preparar pruebas automatizadas y registrar limitaciones sin atribuirse trabajo de Gemini.
- **Canal compartido:** Google Doc `CHATS_Gemini_GPT.md` en Drive, con mensajes `[TEAM-N]`, autor, fecha y respuesta al ID. Google Docs se usa cuando cada agente está activo; no es una conexión permanente ni un webhook.

## Primera contribución de ChatGPT en la rama de prueba

1. `cloud/matick_cloud/client.py`: añadir comando `health` que consulta `GET /health` sin requerir `MATICK_TOKEN`, evitando transmitir un token a la ruta pública.
2. `cloud/tests/test_cloud.py`: confirmar diagnóstico público, rechazo de `/v1/status` sin token y consulta autenticada con identidad correcta.
3. Mantener intactos los contratos HTTP actuales del servidor y los roles; no introducir secretos ni servicios externos.
4. Verificar con `PYTHONPATH=cloud python -m unittest discover -s cloud/tests -v` (GitHub Actions). La compilación Windows DX12 se comprueba por separado en el CI.

**Esto no implementa todavía el panel DX12**, las conexiones Gemini/ChatGPT con el servidor ni la recepción automática de documentos. La propuesta visual de Gemini es un entregable independiente pendiente de recepción real.

## Entrega esperada de Gemini

Publicar una nueva entrada en el chat central respondiendo al proyecto **Matick Studio LM Cloud** con: diseño de cuatro estados (Conectado, Desconectado, En desarrollo, No configurado), localización del indicador de salud, experiencia ante fallo y recuperación, cambios sugeridos sin romper el diseño DX12 existente, criterios visuales y riesgos. Enlazar el mensaje desde este documento o el PR cuando exista.

## Criterios de aceptación

- El CLI `health` da estado sin token con un servidor local válido.
- El CLI `status` y los demás comandos siguen requiriendo token.
- Las pruebas de regresión pasan en CI.
- Las propuestas de Gemini se leen desde Drive y se atribuyen solo tras verificarse; no inventar que llegaron.
- Morlet puede comparar esta rama con `main`, revisar el PR y revertir cerrándolo o descartando la rama.

## Estado inicial

- Código del comando `health`: **implementado en rama de prueba**; pruebas CI por confirmar.
- Diseño de Gemini: **pendiente**.
- Intercambio documental de extremo a extremo para este proyecto: **pendiente de respuesta de Gemini**.
