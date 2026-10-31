# Matick Studio LM: identidad independiente y herramientas MCP propias

**Matick Studio LM es un producto nuevo**, no una modificación ni una copia de LM Studio, ChatGPT o Codex. Su API propia es Matick REST v1, publicada en las rutas /v1/ del servidor Matick.

## Componentes propios

- Matick Core: API autenticada, SQLite, chat, ajustes y tareas.
- Matick Work y DirectX 12: interfaces desarrolladas en este repositorio.
- Matick MCP Bridge: servidor stdio JSON-RPC original escrito con Python estándar, sin librerías externas.
- Matick ToolHub: cliente propio de Matick REST v1 y conectores MCP que se activan con permiso.

## Usar herramientas Matick en LM Studio u otro host MCP

LM Studio admite servidores MCP a través de su archivo mcp.json; referencia del formato: https://lmstudio.ai/docs/app/mcp . Esto es interoperabilidad, NO afiliación ni reutilización de su motor.

1. Iniciar el servidor propio de Matick con autenticación. El valor predeterminado de prueba es http://127.0.0.1:8787.
2. Abrir en el host MCP su editor de mcp.json. En LM Studio suele estar en Program → Install → Edit mcp.json.
3. Copiar la sección de integrations/matick-mcp/mcp.example.json al mcp.json local. CAMBIAR la ruta Python de ejemplo por la ubicación real del script.
4. Proporcionar MATICK_TOKEN al proceso anfitrión por su entorno o gestor local de secretos. Nunca guardarlo en GitHub.
5. Probar primero matick_health, matick_capabilities, matick_models y matick_tasks.

Se incluyen además matick_create_task y matick_ask, pero están **desactivadas por defecto**. Para habilitarlas conscientemente, configurar MATICK_MCP_ALLOW_TASK_CREATE=1 o MATICK_MCP_ALLOW_CHAT=1 en el entorno local del puente.

El puente NO controla mouse, teclado, filesystem ni ejecuta comandos arbitrarios. No carga modelos ni copia CUDA. Las respuestas MCP son datos no confiables, no instrucciones superiores.

## Cómo comprobar el protocolo sin host

Desde una terminal ejecutar: python integrations/matick-mcp/matick_mcp.py . Lee JSON-RPC por stdin y escribe JSON-RPC por stdout. Para probar de forma reproducible, ejecutar las pruebas de Python en cloud/tests/test_matick_mcp.py.

## Derechos y compatibilidad

Se usan protocolos documentados (MCP, JSON-RPC, HTTP), no código fuente ni bibliotecas del producto tercero. El código propio conserva su licencia Apache-2.0. Los nombres LM Studio, OpenAI, ChatGPT y Codex se mencionan solo como marcas ajenas y referencias de interoperabilidad. Antes de distribución final debe revisarse la licencia de cada recurso incorporado.

## Estado verificable

Matick dispone de su propio plano de control. Todavía NO dispone de inferencia nativa independiente: el chat sigue necesitando un proveedor de inferencia configurado. Tampoco están verificadas Alexa, Galaxy Fit3, Matick Codex autónomo ni la mascota original.
