# Matick Studio LM Cloud v1.0.1 — Instalador Windows x64

Este ZIP contiene **MatickStudioLM-v1.0.1-x64-Setup.exe** (instalador Windows) y un informe SHA-256. El instalador no necesita Python, Node, LM Studio ni Inno Setup en el PC de destino.

## Instalación

1. Extrae el ZIP en Descargas.
2. Verifica la integridad del instalador (opcional): `Get-FileHash .\MatickStudioLM-v1.0.1-x64-Setup.exe -Algorithm SHA256`.
3. Ejecuta `MatickStudioLM-v1.0.1-x64-Setup.exe`, confirma el editor si Windows SmartScreen lo advierte. **No está firmado digitalmente**: verifica el repositorio y su SHA antes de ejecutarlo.
4. Se instala **solo para tu usuario**, por defecto en `%LOCALAPPDATA%\Programs\Matick Studio LM Cloud`. No requiere permisos de administrador.
5. Abre **Matick Studio LM Cloud** desde Inicio. La ventana DirectX 12 se muestra primero; si falla DirectX pasa a modo seguro GDI. El backend ligero Python 3.12.10 se inicia automáticamente por el propio programa.
6. El navegador `http://127.0.0.1:8787/app` muestra Matick Work. Para chatear con un modelo debes configurar un proveedor real de inferencia; el instalador no contiene pesos ni descarga modelos.

**IMPORTANTE:** si tienes otro programa ya usando el puerto 8787, el servidor de Matick podría no iniciar. Matick nunca mata ese proceso ni cambia el puerto sin permiso.

## Desinstalación segura

En Windows 11: **Configuración → Aplicaciones → Aplicaciones instaladas → Matick Studio LM Cloud → Desinstalar**.

O desde Inicio busca el acceso a desinstalar (si aparece en el menú del sistema). El desinstalador de Inno Setup elimina únicamente archivos instalados por Matick en su carpeta de programa. No borra:

- `C:\IA\Matick Studio LM` (tu versión principal en desarrollo).
- `C:\IA\modelos`, GGUF, checkpoints, datasets u otros recursos personales.
- `%LOCALAPPDATA%\MatickStudioLM\data` (SQLite, preferencias si existen).
- `%LOCALAPPDATA%\MatickStudioLM\logs` (registros para diagnóstico).

Estos datos se mantienen para una reinstalación posterior. Si quisieras eliminarlos, respáldalos y hazlo manualmente.

## Detalles técnicos

- EXE Windows **x64**, MSVC, render Direct3D 12 con fallback Win32 GDI.
- Matick Core Python estándar 3.12.10 embebido en `runtime`, verificado mediante SHA256 y aislado con `python312._pth`.
- Backend local temporal bajo un **Job Object de Windows**: se inicia al abrir Matick y termina al cerrar esa instancia, sin dejar servicios permanentes ni modificar firewall/registro.
- La base SQLite vive en `%LOCALAPPDATA%\MatickStudioLM\data\events.sqlite`; el backend registra en `...\logs\backend.log`.
- No hay servicio Windows global, instalación de Python global, instalación npm, CUDA incluida ni modificación de otras aplicaciones.
- Inno Setup registra la desinstalación de Matick en el perfil de usuario. No requiere Inno Setup instalado para usarlo.

## Pruebas y limitaciones

GitHub Actions compila x64, verifica sintaxis y tests, prepara runtime Python embebido, genera el instalador Inno Setup, prueba instalación silenciosa en Windows y verifica que el desinstalador deja intactos datos externos. La evaluación final del render con tu RTX 5060, drivers, protección antivirus y modelos GGUF requiere una prueba real en MORLET-GAMING.

**Python 3.12.10:** PSF License (licencia incluida en `runtime\LICENSE.txt`). El runtime se descarga solo durante la compilación de GitHub, no durante la instalación en tu PC. Cuando se actualice Python, será necesario reconstruir el instalador.
