# Arquitectura — Matick Studio LM

## Límites

**Matick Studio LM** es una plataforma propia, separada de **LM Studio** (producto externo de ejecución local de modelos). El repositorio está orientado al plano de control en la nube y a su interfaz nativa Windows. Ningún nombre de endpoint debe hacerse pasar por una integración operativa si no hay credenciales, puente o servicio conectado.

```text
                     +------------------------+
                     | Matick Studio LM Cloud |
                     | director / eventos / SQLite|
                     +-----------+------------+
                                 |
             Enlaces independientes por identidad y token
       +-------------+-----------+------------+----------------+
       |             |           |            |                |
   ChatGPT       Matick Chat  Matick Codex  Matick Reloj       Alexa
       |             |           |            |                |
       +-------------+-----------+------------+----------------+
                                 |
                       Matick Pet (solo estado)
                         Cliente Windows
                         MatickStudioLM.exe
                         Direct3D 12 / WinHTTP
```

**El diagrama muestra el contrato y la ruta de dirección**, no conexiones actualmente configuradas. Cada componente se comunica directamente con el servicio cloud, sin exigir pasar por ChatGPT. Matick Studio LM y ChatGPT pueden dirigir eventos a los demás componentes. Alexa conserva la ruta preferida Alexa → ChatGPT cuando su adaptador esté instalado. La conexión ChatGPT ↔ Matick Studio LM requiere un conector autorizado; este repositorio por sí solo no la habilita.

Matick Pet es un destino de **estado operativo de solo lectura**. El rol `matick-pet` no puede publicar eventos. El bus acepta `status.snapshot` únicamente desde `matick-studio-lm`, con los campos `component`, `state` (`idle`, `working`, `waiting`, `error` u `offline`), `updated_at` con zona horaria y `progress_pct` opcional de 0 a 100. Aún hace falta un adaptador que transforme ese evento en una actualización visible de la mascota de ChatGPT Work. No se permiten campos extra ni se envían datos de salud en este evento.

## Contrato HTTP v1

- `GET /health`: comprobación pública, sin información secreta.
- `GET /v1/status`: exige `Authorization: Bearer TOKEN_DEL_ROL`; devuelve el rol autenticado.
- `GET /v1/routes`: exige token y devuelve los destinos autorizados del rol.
- `POST /v1/events`: token del rol emisor; JSON `{"target":"matick-chat","kind":"mensaje","payload":{"texto":"hola"}}`; el servidor fija `source` a partir del token, nunca del cuerpo.
- `POST /v1/direct`: solo roles directores (`matick-studio-lm` y `chatgpt`); JSON `{"targets":["matick-chat","matick-codex"],"kind":"tarea.asignada","payload":{"id":"t-1"}}`. Distribuye el mismo evento a destinos explícitos y devuelve el ID de cada entrega. No admite comodines.
- `GET /v1/events?after=0&limit=50`: token del rol receptor; entrega exclusivamente mensajes destinados a ese rol, por ID ascendente. El cliente debe conservar su cursor.
- Respuesta 201 de `POST /v1/events`: `{"id":123,"source":"matick-studio-lm","target":"matick-chat"}`.

Roles del MVP: `matick-studio-lm`, `chatgpt`, `matick-chat`, `matick-codex`, `matick-reloj`, `alexa`, `windows-dx12` y `matick-pet`.

## Política de dirección

- Matick Studio LM y ChatGPT pueden dirigir eventos a destinos explícitos permitidos por sus roles.
- Matick Chat, Matick Codex, Matick Reloj, Alexa y la app Windows pueden enviar eventos a Matick Studio LM y ChatGPT.
- Matick Pet solo recibe `status.snapshot` desde Matick Studio LM; no tiene permisos de escritura ni de ejecución.
- Cada componente debe usar su propio token. Los adaptadores externos aún deben implementar autenticación, validación de entrada y control de reintentos.
- La dirección mueve eventos; no decide acciones con un modelo ni ejecuta comandos. Un agente destino valida permisos y decide qué hacer.

Los eventos son **datos**, no comandos automáticamente ejecutados. Un agente que quiera operar Windows necesita un puente local explícitamente autorizado, control de permisos, confirmaciones para operaciones de riesgo y parada de emergencia.

## Seis frentes de implementación

1. **Arquitectura:** API versionada, almacenamiento, eventos y contratos de integración.
2. **Cloud:** despliegue HTTPS, identidad por componente, observabilidad y continuidad.
3. **DirectX 12:** `.exe` x64 nativo con paneles, accesibilidad y red.
4. **Matick Codex:** ejecutar tareas en entornos aislados, con aprobaciones y registros.
5. **Integraciones:** ChatGPT, Alexa, teléfono, reloj y Matick Chat mediante adaptadores.
6. **Pruebas y distribución:** CI, compilación de Windows, seguridad y actualizaciones.

## Límites del MVP

El transporte usa **polling HTTP**, no WebSocket. SQLite persiste mensajes entre reinicios si se conserva `MATICK_DB_PATH`. El MVP ya aplica una matriz básica de rutas, pero no tiene borrado por retención, rate limit, login OAuth, inferencia de IA, comandos remotos ni conexión funcional con proveedores externos. La mascota aún no tiene adaptador. Todo ello son tareas posteriores, no características afirmadas como completas.

## Versionado

API `/v1`. Mantener contratos compatibles y probarlos antes de introducir cambios. Los clientes deberán usar `MATICK_CLOUD_URL` apuntando a un host seguro de producción, no a una IP privada fija.

