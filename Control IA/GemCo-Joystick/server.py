# -*- coding: utf-8 -*-
"""GemCo Joystick 0.1 - servidor MCP stdio, Windows, Python >=3.11.
MCP transporta comandos de alto nivel; el control del juego ocurre localmente.
No ejecuta comandos shell, no eleva permisos y no intenta saltar protecciones.
"""
import base64
import json
import math
import os
import re
import sys
import threading
import time
from pathlib import Path

ROOT = Path.home() / ".gemco" / "joystick"
ROOT.mkdir(parents=True, exist_ok=True)
CONTROL = ROOT / "control.json"
PROFILE = ROOT / "perfil.json"
SESSION = ROOT / "sesion.json"
CAPTURES = ROOT / "capturas"
CAPTURES.mkdir(exist_ok=True)
LOCK = threading.RLock()
PAD = None
TIMER = None
CURRENT_BUTTONS = []
IMAGE_PREVIOUS = None
SAFE_KEYS = set("abcdefghijklmnopqrstuvwxyz0123456789") | {
    "up","down","left","right","space","enter","tab","esc",
    "shift","ctrl","backspace","f1","f2","f3","f4","f5","f6",
    "f7","f8","f9","f10","f11","f12"
}
BUTTONS = {
    "a":"XUSB_GAMEPAD_A","b":"XUSB_GAMEPAD_B","x":"XUSB_GAMEPAD_X",
    "y":"XUSB_GAMEPAD_Y","lb":"XUSB_GAMEPAD_LEFT_SHOULDER",
    "rb":"XUSB_GAMEPAD_RIGHT_SHOULDER","start":"XUSB_GAMEPAD_START",
    "back":"XUSB_GAMEPAD_BACK","ls":"XUSB_GAMEPAD_LEFT_THUMB",
    "rs":"XUSB_GAMEPAD_RIGHT_THUMB","up":"XUSB_GAMEPAD_DPAD_UP",
    "down":"XUSB_GAMEPAD_DPAD_DOWN","left":"XUSB_GAMEPAD_DPAD_LEFT",
    "right":"XUSB_GAMEPAD_DPAD_RIGHT",
}
DEFAULT_PROFILE = {"speed":"balanced","reasoning":"balanced",
                   "capture_width":960,"action_ms":160,
                   "camera_sensitivity":1.0,"observations":0,
                   "avg_latency_ms":0}
def read(path, fallback):
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else dict(fallback)
    except (OSError, ValueError, TypeError):
        return dict(fallback)

def write(path, obj):
    with LOCK:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)

def config():
    data = read(PROFILE, DEFAULT_PROFILE)
    return {**DEFAULT_PROFILE, **data}

def control():
    return read(CONTROL, {"armed_until":0,"stopped":True})

def allowed():
    c = control()
    return not c.get("stopped", True) and time.time() < float(c.get("armed_until", 0))

def need_armed():
    if not allowed():
        raise PermissionError("DESARMADO: abre panel.py, presiona ARMAR (máximo 10 minutos)")

def fnum(v, low=-1.0, high=1.0):
    n = float(v)
    if not math.isfinite(n) or not low <= n <= high:
        raise ValueError("Número fuera del intervalo")
    return n

def release_pad():
    global TIMER, PAD
    with LOCK:
        if TIMER:
            TIMER.cancel()
            TIMER = None
        if PAD is not None:
            try: PAD.reset(); PAD.update()
            except Exception: pass

def stop_all():
    c = control()
    c.update({"stopped":True,"armed_until":0})
    write(CONTROL, c)
    release_pad()
    return {"ok":True,"stopped":True}

def gamepad():
    global PAD
    if PAD is None:
        try:
            import vgamepad as vg
            PAD = vg.VX360Gamepad()
        except Exception as exc:
            raise RuntimeError("Requiere vgamepad + ViGEmBus instalado y autorizado por Windows: " + str(exc))
    return PAD

def action_gamepad(lx=0,ly=0,rx=0,ry=0,lt=0,rt=0,buttons=None,hold_ms=None):
    """Envía un estado XInput con dos sticks, gatillos y botones durante 30-800 ms."""
    global TIMER, CURRENT_BUTTONS
    need_armed()
    import vgamepad as vg
    p = gamepad()
    prof = config()
    ms = int(hold_ms if hold_ms is not None else prof["action_ms"])
    if not 30 <= ms <= 800: raise ValueError("hold_ms debe estar entre 30 y 800")
    b = [x.lower() for x in (buttons or [])]
    if len(b) > 12 or any(x not in BUTTONS for x in b):
        raise ValueError("Botón desconocido: " + ", ".join(BUTTONS))
    sens = fnum(prof["camera_sensitivity"], 0.2, 3.0)
    with LOCK:
        if TIMER: TIMER.cancel()
        p.reset()
        p.left_joystick_float(x_value_float=fnum(lx), y_value_float=fnum(ly))
        p.right_joystick_float(x_value_float=max(-1,min(1,fnum(rx)*sens)),
                               y_value_float=max(-1,min(1,fnum(ry)*sens)))
        p.left_trigger_float(value_float=fnum(lt,0,1))
        p.right_trigger_float(value_float=fnum(rt,0,1))
        for name in b: p.press_button(button=getattr(vg.XUSB_BUTTON, BUTTONS[name]))
        p.update()
        CURRENT_BUTTONS = b
        TIMER = threading.Timer(ms/1000, release_pad)
        TIMER.daemon = True
        TIMER.start()
    return {"ok":True,"hold_ms":ms,"buttons":b,"auto_release":True}

def keyboard(keys, duration_ms=100):
    """Pulsa teclas permitidas sin atajos de sistema; liberar siempre tras el intervalo."""
    need_armed()
    try: import pydirectinput as di
    except ImportError: raise RuntimeError("Falta pydirectinput: pip install pydirectinput")
    names = [str(v).lower().strip() for v in keys]
    if not names or len(names) > 3 or any(k not in SAFE_KEYS for k in names):
        raise ValueError("Teclas no permitidas. No se admiten atajos de administración.")
    duration_ms = int(duration_ms)
    if not 30 <= duration_ms <= 700: raise ValueError("Duración fuera de rango (30..700 ms)")
    pressed = []
    try:
        for k in names:
            di.keyDown(k); pressed.append(k)
        time.sleep(duration_ms/1000)
    finally:
        for k in reversed(pressed):
            try: di.keyUp(k)
            except Exception: pass
    return {"ok":True,"keys":names,"duration_ms":duration_ms}

def mouse(dx=0,dy=0,button="none"):
    """Movimiento relativo limitado + clic; nunca captura ni exporta datos del usuario."""
    need_armed()
    try: import pydirectinput as di
    except ImportError: raise RuntimeError("Falta pydirectinput")
    dx,dy = int(dx),int(dy)
    if abs(dx) > 600 or abs(dy) > 600: raise ValueError("Movimiento demasiado grande")
    if button not in ("none","left","right","middle"):
        raise ValueError("Botón inválido")
    if dx or dy: di.moveRel(dx,dy,duration=0)
    if button != "none": di.click(button=button)
    return {"ok":True,"dx":dx,"dy":dy,"button":button}

def screenshot(as_image=False, monitor=1):
    """Captura bajo demanda. Devuelve JPG a visión solo con as_image=true."""
    global IMAGE_PREVIOUS
    try:
        import mss
        from PIL import Image, ImageChops, ImageStat
    except ImportError: raise RuntimeError("Requiere mss y Pillow: pip install mss Pillow")
    with mss.mss() as s:
        monitor = int(monitor)
        if monitor < 1 or monitor >= len(s.monitors): raise ValueError("Monitor no disponible")
        img = s.grab(s.monitors[monitor])
        im = Image.frombytes("RGB", img.size, img.rgb)
    width = int(config()["capture_width"])
    if im.width > width:
        im.thumbnail((width, max(1,int(im.height*width/im.width))))
    stamp = int(time.time()*1000)
    path = CAPTURES / f"frame-{stamp}.jpg"
    im.save(path, "JPEG", quality=68, optimize=True)
    files = sorted(CAPTURES.glob("frame-*.jpg"))
    for old in files[:-20]:
        try: old.unlink()
        except OSError: pass
    change = None
    if IMAGE_PREVIOUS is not None and IMAGE_PREVIOUS.size == im.size:
        previous = IMAGE_PREVIOUS
        thumb1 = im.resize((64,36)).convert("L")
        thumb0 = previous.resize((64,36)).convert("L")
        diff = ImageStat.Stat(ImageChops.difference(thumb1, thumb0)).mean[0]
        change = round(diff/255,4)
    IMAGE_PREVIOUS = im.copy()
    info = {"ok":True,"file":str(path),"width":im.width,
            "height":im.height,"change_ratio":change,"sent_to_cloud":False}
    if as_image:
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return info, {"type":"image","data":data,"mimeType":"image/jpeg"}
    return info, None

def profile_update(speed="balanced", reasoning="balanced"):
    if speed not in ("fast","balanced","precise"): raise ValueError("speed inválido")
    if reasoning not in ("low","balanced","high"): raise ValueError("reasoning inválido")
    p = config()
    p["speed"],p["reasoning"] = speed,reasoning
    # Ajustes de captura y duración; no son ajustes internos de LM Studio.
    p["capture_width"] = {"fast":640,"balanced":960,"precise":1280}[speed]
    p["action_ms"] = {"fast":90,"balanced":160,"precise":230}[speed]
    write(PROFILE,p)
    return p

def session_start(game="juego"):
    if not re.fullmatch(r"[\w .-]{1,60}",game,re.UNICODE):
        raise ValueError("Nombre de juego inválido")
    obj = {"game":game,"started_at":int(time.time()),"feedback":[],
           "actions":0,"notes":"Feedback mejora parámetros de control, no reentrena pesos LLM."}
    write(SESSION,obj)
    return {"ok":True,"session":game}

def session_feedback(reward=0.0, latency_ms=0, note=""):
    """Autoajusta parámetros heurísticos con recompensa externa; no cambia pesos del modelo."""
    reward = fnum(reward,-1,1)
    latency_ms = int(fnum(latency_ms,0,60000))
    obj = read(SESSION,{})
    if not obj.get("game"): raise ValueError("Inicia una sesión")
    prof = config()
    count = int(prof.get("observations",0))
    avg = float(prof.get("avg_latency_ms",0))
    avg = avg*0.8 + latency_ms*0.2 if count else latency_ms
    prof["avg_latency_ms"] = round(avg,1)
    prof["observations"] = count+1
    # Ajuste conservador: solo parámetros de ejecución, con límites.
    ms = int(prof["action_ms"])
    if reward < -0.3: ms = max(60,ms-10)
    elif reward > 0.3 and avg < 1000: ms = min(320,ms+5)
    prof["action_ms"] = ms
    obj["feedback"].append({"t":int(time.time()),"reward":reward,
                            "latency_ms":latency_ms,"note":str(note)[:160]})
    obj["feedback"] = obj["feedback"][-200:]
    write(PROFILE,prof)
    write(SESSION,obj)
    return {"ok":True,"samples":len(obj["feedback"]),
            "action_ms":ms,"avg_latency_ms":avg}

def status():
    try: import vgamepad; pad_available=True
    except ImportError: pad_available=False
    try: import mss; capture_available=True
    except ImportError: capture_available=False
    try: import pydirectinput; keyboard_available=True
    except ImportError: keyboard_available=False
    return {"service":"gemco-joystick","version":"0.1.0",
            "armed":allowed(),"gamepad_library":pad_available,
            "capture_library":capture_available,"keyboard_library":keyboard_available,
            "profile":config(),"session":read(SESSION,{}),
            "controls":"MCP tools, local arming panel, emergency Ctrl+Alt+F12",
            "cloud":"off by default"}

def emergency_hotkey():
    if sys.platform != "win32": return
    import ctypes
    key = ctypes.windll.user32.GetAsyncKeyState
    latched = False
    while True:
        try:
            pressed = bool(key(0x11)&0x8000 and key(0x12)&0x8000 and key(0x7B)&0x8000)
            if pressed and not latched: stop_all()
            latched=pressed
        except Exception: pass
        time.sleep(0.05)

def tool(name, description, props=None, required=None):
    return {"name":name,"description":description,
            "inputSchema":{"type":"object","properties":props or {},
                           "required":required or [],"additionalProperties":False}}
def arg(type_,description,**extra):
    return {"type":type_,"description":description,**extra}
NUM = lambda description:arg("number",description)
STR = lambda description:arg("string",description)
TOOLS = [
    tool("gemco_status","Capacidades locales, perfil, sesión y permiso para manejar el juego."),
    tool("gemco_stop","Parada de emergencia: suelta joystick y desarma cualquier acción."),
    tool("gemco_gamepad","Control Xbox 360 virtual. Requiere armar en panel y vgamepad/ViGEmBus.",
        {**{k:NUM("Eje -1 a 1") for k in ("lx","ly","rx","ry")},
         **{k:NUM("Gatillo 0 a 1") for k in ("lt","rt")},
         "buttons":arg("array","Botones XInput: a,b,x,y,lb,rb,start,back,ls,rs,up,down,left,right",
                       items={"type":"string"}),"hold_ms":arg("integer","30..800 ms; soltado automático")}),
    tool("gemco_keyboard","Teclas de juego permitidas durante 30-700 ms, sin atajos de sistema.",
         {"keys":arg("array","Teclas",items={"type":"string"}),
          "duration_ms":arg("integer","Duración en ms")},["keys"]),
    tool("gemco_mouse","Mover mouse relativo y click simple, sin privilegios extra.",
         {"dx":arg("integer","Pixeles horizontales"),
          "dy":arg("integer","Pixeles verticales"),
          "button":STR("none,left,right,middle")}),
    tool("gemco_screen","Captura local JPG. Para visión enviar as_image=true solo si hace falta.",
         {"as_image":arg("boolean","Por defecto false: responde solo metadatos"),
          "monitor":arg("integer","Monitor 1..n")}),
    tool("gemco_profile","Cambiar velocidad y razonamiento del planificador externo, no LLM interno.",
         {"speed":STR("fast,balanced,precise"),
          "reasoning":STR("low,balanced,high")}),
    tool("gemco_session","Comienza sesión de aprendizaje heurístico para un juego.",
         {"game":STR("Nombre de juego, sin rutas")}),
    tool("gemco_feedback","Aprendizaje por recompensa: -1 fallo a +1 éxito, latencia observada en ms.",
         {"reward":NUM("-1..1"),
          "latency_ms":arg("integer","0..60000"),
          "note":STR("Nota breve opcional")},["reward"]),
    tool("gemco_help","Guía de operación integrada para agentes (no necesita prompt largo)."),
]
HELP = ("Flujo: gemco_status → usuario pulsa ARMAR en panel.py → gemco_session "
        "→ gemco_screen → acción de 30-800ms → gemco_screen → gemco_feedback. "
        "Usar gemco_gamepad para sticks y botones, gemco_keyboard/mouse solo en juegos "
        "que no aceptan XInput. Captura JPG bajo demanda; change_ratio no demuestra éxito. "
        "El razonamiento indicado es preferencia del orquestador, no modifica el modelo. "
        "Ctrl+Alt+F12 detiene; gemco_stop también. Solo juegos locales/autorizados. "
        "No se hacen elevaciones, no se evaden anticheat, no se exponen puertos.")
CALLS = {
    "gemco_status":lambda a:status(),
    "gemco_stop":lambda a:stop_all(),
    "gemco_gamepad":lambda a:action_gamepad(**a),
    "gemco_keyboard":lambda a:keyboard(**a),
    "gemco_mouse":lambda a:mouse(**a),
    "gemco_screen":lambda a:screenshot(**a),
    "gemco_profile":lambda a:profile_update(**a),
    "gemco_session":lambda a:session_start(**a),
    "gemco_feedback":lambda a:session_feedback(**a),
    "gemco_help":lambda a:{"guide":HELP},
}
def emit(obj):
    sys.stdout.write(json.dumps(obj,ensure_ascii=False,separators=(",",":"))+"\n")
    sys.stdout.flush()
def serve():
    threading.Thread(target=emergency_hotkey,name="gemco-emergency",
                     daemon=True).start()
    for line in sys.stdin:
        try:
            req = json.loads(line)
            ident = req.get("id")
            name = req.get("method")
            if ident is None: continue
            params = req.get("params") or {}
            if name == "initialize":
                result = {"protocolVersion":"2025-03-26",
                          "capabilities":{"tools":{"listChanged":False}},
                          "serverInfo":{"name":"gemco-joystick","version":"0.1.0"}}
            elif name == "ping": result = {}
            elif name == "tools/list": result = {"tools":TOOLS}
            elif name == "tools/call":
                target = params.get("name")
                if target not in CALLS: raise ValueError("Herramienta desconocida")
                args = params.get("arguments") or {}
                if not isinstance(args,dict): raise ValueError("Argumentos inválidos")
                try:
                    out = CALLS[target](args)
                    image = None
                    if isinstance(out,tuple): out,image=out
                    content = [{"type":"text","text":json.dumps(out,ensure_ascii=False)}]
                    if image: content.append(image)
                    result = {"content":content,"isError":False}
                except Exception as e:
                    result = {"content":[{"type":"text","text":str(e)}],"isError":True}
            elif name in ("resources/list","prompts/list"):
                result = {"resources":[] } if name=="resources/list" else {"prompts":[]}
            else:
                emit({"jsonrpc":"2.0","id":ident,
                      "error":{"code":-32601,"message":"Método no disponible"}})
                continue
            emit({"jsonrpc":"2.0","id":ident,"result":result})
        except Exception as e:
            try: emit({"jsonrpc":"2.0","id":req.get("id") if isinstance(req,dict) else None,
                       "error":{"code":-32603,"message":str(e)}})
            except Exception: pass

if __name__=="__main__":
    if "--self-test" in sys.argv:
        print(json.dumps(status(),ensure_ascii=False,indent=2))
    else:
        serve()
