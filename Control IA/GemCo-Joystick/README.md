# GemCo Joystick 0.1 | Habilidad MCP para Windows 11

Control local y gratuito de joystick virtual tipo Xbox, teclado, mouse y capturas, con memoria por sesión.

**Instalación solicitada:** C:\Program Files\LM Studio\Habilidades\GemCo-Joystick

## Archivos

* server.py: MCP stdio, 10 herramientas (estado, parada, joystick, teclado, mouse, pantalla, perfiles, inicio de sesión, feedback y ayuda).
* panel.py: panel gráfico para autorizar por diez minutos, detener y ajustar perfiles.
* learning.py: memoria local de experiencias por juego con recomendaciones UCB. **Es un módulo experimental independiente; todavía no lo expone server.py como herramienta MCP.**
* mcp.json: conserva 7 servidores originales de Matick y agrega gemco-joystick.
* instalar.ps1: copia archivos y respalda mcp.json antes de insertar la herramienta.
* requirements.txt: mss, Pillow y pydirectinput. Xbox opcional utiliza vgamepad y ViGEmBus.

## Instalar

1. En GitHub ve a Code → Download ZIP. Extrae el repositorio y abre la carpeta Control IA/GemCo-Joystick.
2. Abre PowerShell como administrador para poder copiar a Program Files. Revisa el instalador antes de ejecutarlo.
3. Desde la carpeta extraída, ejecuta el siguiente comando, poniendo la ruta real de tu MCP JSON:

    .\instalar.ps1 -InstallDependencies -VirtualXbox -McpJsonPath "RUTA_REAL\mcp.json"

El parámetro -VirtualXbox es opcional y puede abrir un instalador de controladores que exige tu permiso en Windows. Si no estás listo para instalar el controlador, omítelo. Si no tienes identificado el archivo MCP original, omite -McpJsonPath: el script conserva la configuración y puedes copiar la entrada manualmente.

Verificación de sólo lectura:

    & "C:\Python315\python.exe" "C:\Program Files\LM Studio\Habilidades\GemCo-Joystick\server.py" --self-test

Abre el panel:

    & "C:\Python315\python.exe" "C:\Program Files\LM Studio\Habilidades\GemCo-Joystick\panel.py"

**Python 3.15:** el MCP se basa en Python estándar, pero algunas dependencias de control pueden no tener ruedas listas para 3.15. En ese caso instala Python 3.12 y pasa -Python "RUTA\python.exe" al instalador. No sustituyas ni desinstales tu Python 3.15.

## Comandos principales

- gemco_status: estado y capacidades del servidor.
- gemco_screen: captura local JPG; as_image=true envia una imagen al cliente MCP solo cuando lo solicita.
- gemco_gamepad: ejes analógicos lx,ly,rx,ry [-1,1], gatillos lt,rt [0,1] y botones Xbox. Dura entre 30 y 800 ms antes de soltar.
- gemco_keyboard y gemco_mouse: teclas y movimientos limitados.
- gemco_session y gemco_feedback: guarda recompensa/latencia para ajustar duración de pulsaciones.
- gemco_profile: fast, balanced, precise. Son perfiles del agente y no cambian parámetros internos del modelo.
- gemco_stop: libera el mando y detiene la autorización.

**Emergencia: Ctrl+Alt+F12** o botón DETENER del panel. El usuario debe ARMAR para emitir acciones.

## Aprendizaje y pesos

La memoria funciona como adaptación por recompensa/latencia y UCB de bajo coste; no reentrena los pesos de Gemma 4. Para control más inteligente, el LLM local decide objetivos ocasionalmente mientras un controlador rápido realiza acciones cortas. Una diferencia entre capturas no prueba que el juego haya avanzado.

Fuentes de estudio, sin incorporar código o pesos de terceros:
- https://github.com/dennishilk/PixelVisionAI (juegos mediante pantalla, aprendizaje por adaptadores)
- https://github.com/adipuscasu/AI.game.agent (captura/visión/estado/teclado)
- https://github.com/DLR-RM/rl-baselines3-zoo (pesos RL y algoritmos para entornos específicos)
- https://github.com/openai/Video-Pre-Training (entrenamiento por video, específico de Minecraft)

**No se pueden fusionar directamente pesos Atari/Minecraft con Resident Evil** porque las observaciones y acciones son diferentes. No se redistribuyen pesos externos ni drivers. vgamepad depende de ViGEmBus, tecnología archivada: evalúa sus riesgos y las licencias antes de instalar.

## Seguridad y estado real

Uso recomendado exclusivamente en juegos offline/autorizados. No elude UAC, protecciones del juego ni anticheat. Capturas y memoria se mantienen en tu PC salvo que tú habilites expresamente su transmisión a un modelo remoto.

Fuente escrita en GitHub; todavía falta probar en tu equipo la instalación, MCP con LM Studio, controlador virtual y juegos reales. El ZIP Jugar IA aprendizaje pequeño.zip aún no es accesible en esta conversación; podremos integrarlo tras adjuntarlo como archivo.
