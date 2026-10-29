# -*- coding: utf-8 -*-
"""Aprendizaje ligero, local y entre juegos (no modifica pesos de LLM).
Políticas contextuales discretas con memoria acotada, UCB y métricas por acción.
"""
import json
import math
import os
import re
import threading
import time
from pathlib import Path
from collections import defaultdict
ROOT=Path.home()/".gemco"/"joystick"/"aprendizaje"
ROOT.mkdir(parents=True,exist_ok=True)
GUARD=threading.RLock()
ACTIONS=("forward","back","strafe_left","strafe_right","turn_left","turn_right",
         "look_up","look_down","attack","interact","jump","dodge","wait")
def normalize(v,kind="name"):
    value=str(v).strip().lower()
    if not re.fullmatch(r"[\w .-]{1,48}",value,re.UNICODE):
        raise ValueError(f"{kind}: usa un nombre corto sin rutas")
    return value
def path_for(game):
    game=normalize(game,"game")
    return ROOT/("g_"+game.encode("utf8").hex()[:96]+".json")
def read(game):
    p=path_for(game)
    if not p.exists(): return {"version":1,"game":normalize(game),"contexts":{},"total":0}
    try:
        d=json.loads(p.read_text(encoding="utf8"))
        if not isinstance(d,dict) or d.get("version")!=1: raise ValueError()
        return d
    except (OSError,ValueError): raise ValueError("Memoria corrupta: revisa el archivo local")
def write(game,d):
    with GUARD:
        p=path_for(game); tmp=p.with_suffix(".tmp")
        tmp.write_text(json.dumps(d,ensure_ascii=False,separators=(",",":")),encoding="utf8")
        os.replace(tmp,p)
def learn(game,scene,action,reward,latency_ms=0):
    """Feedback externo: no inferir éxito de una captura por sí sola."""
    game=normalize(game,"game")
    scene=normalize(scene,"scene")
    action=normalize(action,"action")
    if action not in ACTIONS: raise ValueError("Acción no reconocida: "+",".join(ACTIONS))
    reward=float(reward)
    if not math.isfinite(reward) or not -1<=reward<=1: raise ValueError("Recompensa -1..1")
    latency_ms=int(latency_ms)
    if not 0<=latency_ms<=60000: raise ValueError("latencia 0..60000")
    with GUARD:
        d=read(game)
        contexts=d.setdefault("contexts",{})
        if scene not in contexts and len(contexts)>=80:
            raise ValueError("Memoria llena: máximo 80 contextos por juego")
        moves=contexts.setdefault(scene,{})
        item=moves.setdefault(action,{"n":0,"sum":0.0,"latency":0.0})
        item["n"]=min(1000000,int(item.get("n",0))+1)
        item["sum"]=round(float(item.get("sum",0))+reward,5)
        item["latency"]=round(float(item.get("latency",0))*0.9+latency_ms*0.1,1)
        d["total"]=min(10000000,int(d.get("total",0))+1)
        d["updated"]=int(time.time())
        write(game,d)
    return {"ok":True,"game":game,"scene":scene,"action":action,"samples":item["n"],
            "mean_reward":round(item["sum"]/item["n"],3),"total":d["total"]}
def recommend(game,scene,top=3):
    game=normalize(game,"game"); scene=normalize(scene,"scene")
    top=int(top)
    if not 1<=top<=5: raise ValueError("top 1..5")
    d=read(game)
    moves=d.get("contexts",{}).get(scene,{})
    n_total=max(1,sum(int(o.get("n",0)) for o in moves.values()))
    ranks=[]
    for a in ACTIONS:
        item=moves.get(a)
        if not item:
            ranks.append({"action":a,"n":0,"expected_reward":None,"score":0.75,"explore":True})
        else:
            n=max(1,int(item["n"]))
            avg=float(item.get("sum",0))/n
            bonus=0.33*math.sqrt(2*math.log(n_total+1)/n)
            ranks.append({"action":a,"n":n,"expected_reward":round(avg,3),
                          "score":round(avg+bonus,3),"explore":False})
    ranks.sort(key=lambda o:(o["score"],-o["n"]),reverse=True)
    return {"game":game,"scene":scene,"suggestions":ranks[:top],
            "known_samples":n_total if moves else 0,
            "note":"Son sugerencias heurísticas; un controlador decide cómo mapear acciones al juego."}
def compact(game,max_chars=600):
    game=normalize(game,"game")
    max_chars=int(max_chars)
    if not 150<=max_chars<=1500: raise ValueError("max_chars 150..1500")
    d=read(game)
    scenes=[]
    for name,moves in d.get("contexts",{}).items():
        if not moves: continue
        best=max(moves.items(),key=lambda pair:float(pair[1].get("sum",0))/max(1,int(pair[1].get("n",1))))
        scenes.append((sum(v.get("n",0) for v in moves.values()),name,best))
    scenes.sort(reverse=True)
    compact_txt=f"GemCo v1; juego={game}; muestras={d.get('total',0)}; "
    for n,scene,(action,o) in scenes:
        text=f"{scene}:{action} n={o['n']} r={round(o['sum']/max(1,o['n']),2)}; "
        if len(compact_txt)+len(text)>max_chars: break
        compact_txt+=text
    return {"summary":compact_txt.strip(),"chars":len(compact_txt)}
