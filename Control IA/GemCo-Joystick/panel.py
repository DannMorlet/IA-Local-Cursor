# -*- coding: utf-8 -*-
"""Panel local GemCo: solo interacción humana puede ARMAR o REARMAR."""
import json
import os
import sys
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

ROOT = Path.home() / ".gemco" / "joystick"
ROOT.mkdir(parents=True,exist_ok=True)
CONTROL = ROOT / "control.json"
PROFILE = ROOT / "perfil.json"
DEFAULT = {"speed":"balanced","reasoning":"balanced",
           "capture_width":960,"action_ms":160,"camera_sensitivity":1.0,
           "observations":0,"avg_latency_ms":0}
def load(path, fallback):
    try: return {**fallback,**json.loads(path.read_text(encoding="utf8"))}
    except Exception: return dict(fallback)
def save(path,data):
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf8")
    os.replace(tmp,path)

app=tk.Tk()
app.title("GemCo · Joystick para IA")
app.geometry("440x420")
app.resizable(False,False)
app.configure(bg="#111827")
tk.Label(app,text="GEMCO  ·  JOYSTICK",font=("Segoe UI",19,"bold"),
         bg="#111827",fg="#eecb70").pack(pady=(16,3))
tk.Label(app,text="Windows local · MCP · Xbox virtual opcional",
         bg="#111827",fg="#cbd5e1").pack()
frame=tk.Frame(app,bg="#111827")
frame.pack(pady=16)
pref=load(PROFILE,DEFAULT)
speed=tk.StringVar(value=pref.get("speed","balanced"))
reason=tk.StringVar(value=pref.get("reasoning","balanced"))
for label,var,opts in [
    ("Velocidad",speed,("fast","balanced","precise")),
    ("Razonamiento externo",reason,("low","balanced","high"))]:
    row=tk.Frame(frame,bg="#111827")
    row.pack(fill="x",pady=5)
    tk.Label(row,text=label,width=21,anchor="w",bg="#111827",
             fg="#e5e7eb").pack(side="left")
    ttk.Combobox(row,textvariable=var,values=opts,
                 width=16,state="readonly").pack(side="right")
def apply_profile():
    p=load(PROFILE,DEFAULT)
    p["speed"],p["reasoning"]=speed.get(),reason.get()
    p["capture_width"]={"fast":640,"balanced":960,"precise":1280}[speed.get()]
    p["action_ms"]={"fast":90,"balanced":160,"precise":230}[speed.get()]
    save(PROFILE,p)
    messagebox.showinfo("GemCo","Perfil aplicado; el servidor MCP lo leerá en el siguiente comando.")
tk.Button(app,text="Guardar perfil",command=apply_profile,width=27,
          bg="#eecb70",fg="#111827").pack(pady=(2,12))
state=tk.StringVar(value="Sin autorización")
tk.Label(app,textvariable=state,font=("Segoe UI",12,"bold"),bg="#111827",
         fg="#f8fafc").pack(pady=6)
def arm():
    save(CONTROL,{"armed_until":time.time()+600,"stopped":False})
    refresh()
def stop():
    save(CONTROL,{"armed_until":0,"stopped":True})
    refresh()
tk.Button(app,text="ARMAR 10 MIN · control IA",command=arm,
          width=27,bg="#93c5fd",fg="#111827").pack(pady=5)
tk.Button(app,text="DETENER Y SOLTAR TODO",command=stop,
          width=27,bg="#fca5a5",fg="#111827").pack(pady=5)
tk.Label(app,text="EMERGENCIA: Ctrl + Alt + F12",
         bg="#111827",fg="#eecb70",font=("Segoe UI",11,"bold")).pack(pady=8)
tk.Label(app,text="Usa en juegos offline/autorizados.\nNo gestiona UAC ni elude anticheat.",
         bg="#111827",fg="#94a3b8").pack()
def refresh():
    c=load(CONTROL,{"armed_until":0,"stopped":True})
    remaining=max(0,int(c.get("armed_until",0)-time.time()))
    state.set(f"ARMADO · {remaining}s restantes" if remaining and not c.get("stopped") else "DESARMADO")
    app.after(1000,refresh)
def on_close():
    stop()
    app.destroy()
app.protocol("WM_DELETE_WINDOW",on_close)
refresh()
app.mainloop()
