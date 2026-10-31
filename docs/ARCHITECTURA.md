# Arquitectura — Matick Studio LM

## Límites

**Aclaración de identidad (octubre 2026):** Matick Core/REST v1/MCP son implementaciones originales, sin SDK de LM Studio en las dependencias principales. Las aplicaciones ajenas son solo clientes MCP o proveedores opcionales mediante interfaces documentadas. [Arquitectura y compatibilidad sin reutilización de código](MATICK_INDEPENDENCIA_Y_MCP.md).


**Matick Studio LM** es una plataforma propia, separada de **LM Studio** (producto externo de ejecución local de modelos). El repositorio está orientado al plano de control en la nube y a su interfaz nativa Windows. Ningún nombre de endpoint debe hacerse pasar por una integración operativa si no hay credenciales, puente o servicio conectado.

```text
                     +------------------------+
                     | Matick Studio LM Cloud |
                     | HTTP / eventos / SQLite|
                     +-----------+------------+
                                 |
             Enlaces independientes por identidad y token
       +-------------+-----------+------------+----------------+
       |             |           |            |                |
   ChatGPT       Matick Chat  Matick Codex  Matick Reloj       Alexa
       |             |           |            |                |
       +-------------+-----------+------------+----------------+
                                 |
                         Cliente Windows
                         MatickStudioLM.exe
                         Direct3D 12 / WinHTTP
```

**El diagrama muestra el contrato planeado**, no conexiones actualmente configuradas. Cada componente se comunica directamente con el servicio cloud, sin exigir pasar por ChatGPT. La ruta preferida para diálogos de Alexa puede seguir siendo Alexa → ChatGPT, una vez que existan sus adaptadores. Los mensajes pueden ir de cualquier rol autorizado a otro. La conexión directa ChatGPT ↔ Matick Studio LM requiere desarrollar e instalar un conector autorizado: este repositorio por sí solo no la habilita.

## Contrato HTTP v1

- `GET /health`: comprobación pública, sin información secreta.
- `GET /v1/status`: exige `Authorization: Bearer TOKEN_DEL_ROL`; devuelve el rol autenticado.
- `POST /v1/events`: token del rol emisor; JSON `{"target":"matick-chat","kind":"mensaje","payload":{"texto":"hola"}}`; el servidor fija `source` a partir del token, nunca del cuerpo.
- `GET /v1/events?after=0&limit=50`: token del rol receptor; entrega exclusivamente mensajes destinados a ese rol, por ID ascendente. El cliente debe conservar su cursor.
- Respuesta 201 de `POST /v1/events`: `{"id":123,"source":"matick-studio-lm","target":"matick-chat"}`.

Roles del MVP: `matick-studio-lm`, `chatgpt`, `matick-chat`, `matick-codex`, `matick-reloj`, `alexa`, `windows-dx12`.

Los eventos son **datos**, no comandos automáticamente ejecutados. Un agente que quiera operar Windows necesita un puente local explícitamente autorizado, control de permisos, confirmaciones para operaciones de riesgo y parada de emergencia.

## Seis frentes de implementación

1. **Arquitectura:** API versionada, almacenamiento, eventos y contratos de integración.
2. **Cloud:** despliegue HTTPS, identidad por componente, observabilidad y continuidad.
3. **DirectX 12:** `.exe` x64 nativo con paneles, accesibilidad y red.
4. **Matick Codex:** ejecutar tareas en entornos aislados, con aprobaciones y registros.
5. **Integraciones:** ChatGPT, Alexa, teléfono, reloj y Matick Chat mediante adaptadores.
6. **Pruebas y distribución:** CI, compilación de Windows, seguridad y actualizaciones.

## Límites del MVP

El transporte usa **polling HTTP**, no WebSocket. SQLite persiste mensajes entre reinicios si se conserva `MATICK_DB_PATH`. No hay borrado por retención, control fino de permisos por destino, rate limit, login OAuth, inferencia de IA, comandos remotos ni conexión funcional con proveedores externos. Todo ello son tareas posteriores, no características afirmadas como completas.

## Versionado

API `/v1`. Mantener contratos compatibles y probarlos antes de introducir cambios. Los clientes deberán usar `MATICK_CLOUD_URL` apuntando a un host seguro de producción, no a una IP privada fija.
