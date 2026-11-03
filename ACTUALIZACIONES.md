# Actualizaciones

## 2026-11-03 — Arranque 1.2 x64 e instalación conservadora

Solicitud: inspección segura del EXE del usuario, coordinación con #58/#56/#47, arranque principal y actualización local preservando datos.

Causas: adjunto apphost .NET1.0 no autónomo; launcher script forzaba configuración externa e impedía bootstrap; empaquetador dependía de RUNNER_TEMP; SQLite dejaba conexiones abiertas en Windows.

Cambios y pruebas detallados en docs/ARRANQUE_V12.md. Backend y recursos en App; EXE1.2 reconstruido desde fuente en raíz. Respaldo previo y conservación de modelos. Fuente del motor fijada a3603dd9 de #58, sin modificar su rama. Compilación x64 y pruebas locales aprobadas; CI se informa por commit. Sin pruebas físicas de RTX5060/DX12/pesos. Pendientes: runtime de inferencia de #58, DPI y validación visual completa.
