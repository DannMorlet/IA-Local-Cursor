# Referencia aprobada: interfaz Matick Studio LM

**Estado:** diseño visual aprobado para implementación incremental. Esta especificación corresponde al mockup seleccionado por el usuario el 30 de octubre de 2026. No implica que los servicios externos estén conectados.

## Diseño visual

- **Barra superior:** Matick Studio LM y pestañas Chat, Trabajo, Codex, Agentes, Modelos, Herramientas.
- **Columna izquierda:** navegación, conversaciones/proyectos y acceso a Manguito, Alexa, Matick Reloj.
- **Zona central clara:** bienvenida, cuadro de instrucciones, accesos rápidos, seis frentes de trabajo, modelos disponibles y actividad.
- **Columna derecha oscura:** mascota robótica con orejas y ojos luminosos, animación suave, estados reales de la API y conectores.
- **Estética:** blanco azulado, azul marino, cian; tipografía Segoe UI; tarjetas simples; interfaz nativa Windows 11, **Direct3D 12** como motor gráfico principal.
- **Rendimiento:** priorizar fluidez en GPU RTX 5060, evitar renderizados pesados y evitar mantener un modelo o servicio cargado si el usuario no lo habilita.

## Lo implementado en este cambio

1. Nuevo layout en el renderer DX12 con tres columnas, tarjetas, barra superior y secciones.
2. Controles Win32: textos, navegación de demostración y cuadro editable de instrucciones.
3. Una **mascota vectorial provisional** dibujada con GDI dentro de la ventana DX12. Sus ojos parpadean de manera periódica.
4. Indicador de API actualizado por la comprobación real de `GET /health`. Las otras integraciones aparecen como pendientes.
5. El botón Enviar muestra una advertencia: no hay modelo cloud implementado y no se envía ningún mensaje.

## Próximos hitos

- Integrar los recursos **originales** de la mascota (no sustituirlos permanentemente por el dibujo provisional) y animaciones expresivas.
- Adaptación DPI, redimensionamiento de paneles, accesibilidad y navegación completa de cada vista.
- Chat real con credenciales delegadas; nunca incrustar tokens secretos en el EXE distribuido.
- Integraciones bidireccionales con Matick Chat, Matick Codex, Matick Reloj y Alexa.
- Métricas GPU/CPU/NPU medidas con APIs reales; no mostrar porcentajes ficticios.
- Validación visual en Windows 11 con GPU RTX 5060.

## Regla de honestidad visual

Se distinguirán cuatro estados: **Conectado** (verificado), **Desconectado**, **En desarrollo** y **No configurado**. No dibujar indicadores verdes por defecto para servicios no disponibles. Los «6 agentes» se representan como áreas de proyecto hasta que existan agentes autónomos efectivamente operativos.

## Nota técnica

El cliente continúa siendo Windows + C++ + Direct3D 12, no Electron ni una página web encapsulada. Win32 es responsable de los textos/controles accesibles y de la mascota vectorial provisional. Esto no reimplementa la aplicación ChatGPT Work, sino que adopta su organización como referencia visual.
