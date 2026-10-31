#!/usr/bin/env python3
# coding: utf-8
"""Matick Studio LM - auditoría de preparación (1..100), solo lectura.
Recorre todos los archivos por metadatos. No ejecuta EXE, scripts ni MCP.
No descarga modelos ni transmite archivos. El resultado se guarda en Descargas.
"""
from __future__ import annotations
import argparse, ast, hashlib, json, os, shutil, struct, sys, time
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

DEFAULT_ROOT = r"C:\IA\Matick Studio LM"
HEAVY = {".gguf",".safetensors",".onnx",".pt",".pth",".engine",".ckpt",".dll",".pdb",".bin",".zip",".7z"}
VENDOR = {"cuda","node_modules","vendor","third_party","external","build",".git",".venv","venv","out","dist"}
SECRET = {".env","mcp.json","secrets.json","credentials.json","token.json"}
REPORT_LIMIT = 50

def private(path):
    return path.name.lower() in SECRET or path.name.lower().startswith(".env.") or any(
        p.lower() in ("secrets",".ssh","credentials") for p in path.parts)

def thirdparty(path):
    return bool({p.lower() for p in path.parts} & VENDOR)

def hash_file(path, limit):
    if path.stat().st_size > limit:
        return None
    d = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            d.update(chunk)
    return d.hexdigest()

def pe_x64(path):
    with path.open("rb") as f:
        if f.read(2) != b"MZ": return False
        f.seek(0x3c)
        data=f.read(4)
        if len(data)!=4:return False
        offset=struct.unpack("<I",data)[0]
        if offset>4*1024*1024:return False
        f.seek(offset)
        if f.read(4)!=b"PE\x00\x00":return False
        machine=f.read(2)
        return len(machine)==2 and struct.unpack("<H",machine)[0]==0x8664

def local_url(address):
    u=urlsplit(address.rstrip("/"))
    if (u.scheme!="http" or u.hostname not in ("localhost","127.0.0.1","::1")
        or u.username or u.password or u.query or u.fragment or u.path not in ("","/")):
        raise ValueError("Solo se permite HTTP por localhost para pruebas.")
    return address.rstrip("/")

def api_json(url, token=None, body=None):
    headers={"Accept":"application/json","User-Agent":"MatickAuditor/1.0"}
    if token:headers["Authorization"]="Bearer "+token
    raw=None
    if body is not None:
        headers["Content-Type"]="application/json"
        raw=json.dumps(body).encode("utf-8")
    try:
        req=Request(url,headers=headers,data=raw,method="POST" if raw is not None else "GET")
        with urlopen(req,timeout=5) as r:return json.loads(r.read(65536))
    except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
        return {"_error":type(e).__name__}

def scan(root, deep=False, max_mb=16):
    files=[];problems=[]
    count={"files":0,"dirs":0,"bytes":0,"hashed":0,"hash_skipped":0,"private":0,
           "heavy":0,"thirdparty":0,"py_checked":0,"py_bad":0,"json_checked":0,
           "json_bad":0,"mcp":0,"mcp_bad":0,"unreadable":0,"symlinks":0}
    limit=(1<<63) if deep else max_mb*1024*1024
    def error(e):
        count["unreadable"]+=1
        problems.append(("Carpeta inaccesible",str(e)))
    for base,dirs,names in os.walk(root,topdown=True,followlinks=False,onerror=error):
        count["dirs"]+=1
        for dirname in dirs[:]:
            if (Path(base)/dirname).is_symlink():
                dirs.remove(dirname)
                count["symlinks"]+=1
        for name in names:
            file=Path(base)/name;rel=file.relative_to(root)
            item={"path":rel.as_posix(),"size":None,"sha256":None,"result":"metadatos"}
            count["files"]+=1
            if file.is_symlink():
                count["symlinks"]+=1;item["result"]="enlace omitido";files.append(item);continue
            try:
                size=file.stat().st_size
                item["size"]=size;count["bytes"]+=size
                protected=private(rel)
                heavy=file.suffix.lower() in HEAVY or thirdparty(rel)
                if protected: count["private"]+=1
                if heavy: count["heavy"]+=1
                if thirdparty(rel):count["thirdparty"]+=1
                if protected:
                    item["result"]="privado: contenido no leído"
                else:
                    digest=hash_file(file,limit)
                    if digest is None:
                        count["hash_skipped"]+=1;item["result"]="hash omitido (grande)"
                    else:
                        count["hashed"]+=1;item["sha256"]=digest;item["result"]="SHA256"
                if not heavy and not protected and size<=2*1024*1024:
                    if file.suffix.lower()==".py":
                        try:
                            ast.parse(file.read_text(encoding="utf-8-sig"),filename=rel.as_posix())
                            count["py_checked"]+=1
                        except (SyntaxError,UnicodeError):
                            count["py_bad"]+=1
                            problems.append(("Python inválido",rel.as_posix()))
                    elif file.suffix.lower()==".json":
                        try:
                            with file.open("r",encoding="utf-8-sig") as f:json.load(f)
                            count["json_checked"]+=1
                        except (ValueError,UnicodeError):
                            count["json_bad"]+=1
                            problems.append(("JSON inválido",rel.as_posix()))
                if file.name.lower()=="mcp.json":
                    count["mcp"]+=1
                    try:
                        if size>1024*1024:raise ValueError("mcp.json grande")
                        with file.open("r",encoding="utf-8-sig") as f:config=json.load(f)
                        if not isinstance(config,dict) or not isinstance(config.get("mcpServers"),dict):
                            raise ValueError("mcpServers inválido")
                    except (ValueError,UnicodeError,OSError):
                        count["mcp_bad"]+=1
                        problems.append(("Configuración MCP inválida",rel.as_posix()))
            except (OSError,PermissionError):
                count["unreadable"]+=1
                item["result"]="inaccesible"
                problems.append(("No se pudo leer",rel.as_posix()))
            files.append(item)
    return files,problems,count

def endpoints(api,lm,smoke):
    url=local_url(api);lms=local_url(lm);token=os.environ.get("MATICK_TOKEN","")
    status=api_json(url+"/health")
    caps=api_json(url+"/v1/capabilities",token) if token else {"_error":"token no configurado"}
    models=api_json(lms+"/api/v1/models",os.environ.get("MATICK_REST_V1_TOKEN",""))
    chat={"_error":"No ejecutada. Opcional: --chat-smoke con MATICK_TOKEN"}
    if smoke and token and "chat" in caps:
        chat=api_json(url+"/v1/chat",token,{"messages":[{"role":"user",
          "content":"Responde brevemente: verificación Matick."}]})
    return {"health":status.get("status")=="ok",
            "auth":"chat" in caps and "_error" not in caps,
            "models":isinstance(models.get("models"),list),
            "model_count":len(models.get("models",[])) if isinstance(models.get("models"),list) else 0,
            "chat":isinstance(chat.get("content"),str) and bool(chat["content"].strip()),
            "chat_info":"respondió" if isinstance(chat.get("content"),str) else chat.get("_error","sin respuesta"),
            "health_info":status.get("_error","ok" if status.get("status")=="ok" else "respuesta inesperada")}

def score_checks(root,m,end,exe_ok):
    tests=[
        ("Carpeta encontrada",8,root.is_dir()),
        ("Inventario de archivos completado",10,m["files"]>0),
        ("Sin archivos inaccesibles",7,m["unreadable"]==0),
        ("Python analizado sin errores",12,m["py_checked"]>0 and m["py_bad"]==0),
        ("JSON analizados sin errores",5,m["json_bad"]==0),
        ("mcp.json estructuralmente válido",8,m["mcp_bad"]==0),
        ("Sin enlaces simbólicos omitidos",5,m["symlinks"]==0),
        ("Python >= 3.11",5,sys.version_info>=(3,11)),
        ("Node disponible",5,shutil.which("node") is not None),
        ("CMake disponible",5,shutil.which("cmake") is not None),
        ("EXE Windows PE x64 válido",10,exe_ok),
        ("Matick /health respondió",5,end["health"]),
        ("API Matick autenticada",5,end["auth"]),
        ("Catálogo LM Studio REST v1",5,end["models"]),
        ("Chat real respondió (opcional)",5,end["chat"]),
    ]
    points=max(1,sum(weight for _,weight,ok in tests if ok))
    return points,[{"test":name,"points":weight,"passed":bool(ok)} for name,weight,ok in tests]

def markdown(root,m,issues,end,score,tests,exe):
    lines=["# Matick Studio LM - Diagnóstico de PC",
           "","Fecha UTC: "+datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "Ruta: "+str(root),"","## Índice de evidencia: %d/100" % score,
           "**No representa el porcentaje real de código correcto.**",
           "No se ha ejecutado MatickStudioLM.exe ni se han modificado archivos.",
           "","## Inventario de TODOS los archivos (metadatos)","",
           "| Medición | Cantidad |","|---|---:|"]
    for name,value in m.items():lines.append("| %s | %s |" %(name,value))
    lines+=["","## Pruebas ponderadas","",
            "| Prueba | Puntos | Estado |","|---|---:|---|"]
    for t in tests:lines.append("| %s | %s | %s |"%(t["test"],t["points"],"OK" if t["passed"] else "No demostrado"))
    lines+=["","## Comprobaciones de ejecución","",
            "- Ejecutable: "+exe,
            "- Servidor /health: "+end["health_info"],
            "- API autenticada: "+str(end["auth"]),
            "- Catálogo REST v1: "+str(end["models"])+" (modelos: %d)"%end["model_count"],
            "- Inferencia de chat: "+end["chat_info"],
            "","## Hallazgos (primeros 50)",""]
    if issues:
        for title,rel in issues[:REPORT_LIMIT]:lines.append("- %s: %s"%(title,rel))
    else:lines.append("- No se encontraron errores en las pruebas estáticas disponibles.")
    lines+=["","## Qué NO puede certificar este informe","",
      "- Interfaz visual, DirectX 12 activo, FPS, estabilidad prolongada ni GPU/NPU.",
      "- Seguridad integral del código, funcionamiento real de todas las herramientas MCP.",
      "- Calidad de respuestas del modelo, velocidades y carga real de VRAM.",
      "- Los archivos grandes se inventarían. Para SHA-256 de TODOS los archivos usa --deep-hash.",
      "","## Siguientes pasos","",
      "1. Revisa advertencias y errores de sintaxis en el informe.",
      "2. Comprueba visualmente el EXE desde una carpeta separada.",
      "3. Configura MATICK_TOKEN y arranca Matick Cloud; repite el diagnóstico.",
      "4. Opcional: añade --chat-smoke para comprobar una respuesta real.",
      "5. Comparte el archivo .md; el inventario .json contiene nombres de todos tus archivos: revísalo antes de compartir.",
      ""]
    return "\n".join(lines)

def main(argv=None):
    p=argparse.ArgumentParser(description="Auditoría Matick Studio LM del 1 al 100, sin escribir en el proyecto.")
    p.add_argument("--root",default=DEFAULT_ROOT)
    p.add_argument("--output",default=None,help="Carpeta NUEVA de informes fuera del proyecto")
    p.add_argument("--deep-hash",action="store_true",help="SHA-256 también para archivos enormes; puede tardar")
    p.add_argument("--max-hash-mb",type=int,default=16)
    p.add_argument("--api-url",default="http://127.0.0.1:8787")
    p.add_argument("--lmstudio-url",default="http://127.0.0.1:1234")
    p.add_argument("--chat-smoke",action="store_true",help="Consulta al modelo real; requiere MATICK_TOKEN")
    a=p.parse_args(argv)
    root=Path(a.root).expanduser().resolve()
    if not root.is_dir():p.error("Carpeta inexistente: "+str(root))
    if not 1<=a.max_hash_mb<=4096:p.error("--max-hash-mb fuera de rango")
    if a.output:
        out=Path(a.output).expanduser().resolve()
    else:
        out=Path.home()/"Downloads"/("Matick_Auditoria_"+datetime.now().strftime("%Y%m%d_%H%M%S"))
    if out==root or root in out.parents:p.error("La salida debe quedar fuera del proyecto local.")
    try:end=endpoints(a.api_url,a.lmstudio_url,a.chat_smoke)
    except ValueError as e:p.error(str(e))
    files,problems,metrics=scan(root,a.deep_hash,a.max_hash_mb)
    exe_candidates=[root/"MatickStudioLM.exe",root/"Matick Studio LM.exe",
       root/"out"/"build"/"Release"/"MatickStudioLM.exe",
       root/"build"/"Release"/"MatickStudioLM.exe",
       root/"bin"/"MatickStudioLM.exe"]
    exe=next((x for x in exe_candidates if x.is_file()),None)
    exe_ok=False;exe_status="No se encontró ejecutable en rutas habituales"
    if exe:
        try:
            exe_ok=pe_x64(exe)
            exe_status=str(exe.relative_to(root))+(": PE x64 válido" if exe_ok else ": cabecera no x64")
        except OSError:exe_status="Error al leer cabecera del ejecutable"
    value,tests=score_checks(root,metrics,end,exe_ok)
    out.mkdir(parents=True,exist_ok=True)
    report=out/"Matick_Resultado_1_a_100.md"
    manifest=out/"Matick_Inventario_Completo.json"
    report.write_text(markdown(root,metrics,problems,end,value,tests,exe_status),encoding="utf-8")
    manifest.write_text(json.dumps({"score":value,"metrics":metrics,
          "checks":tests,"files":files},ensure_ascii=False,indent=2),encoding="utf-8")
    print("Matick - pruebas comprobadas: %d/100" % value)
    print("Archivos inventariados:",metrics["files"]," SHA-256:",metrics["hashed"])
    print("Reporte:",report)
    print("Inventario:",manifest)
    print("Los archivos del proyecto NO se han modificado.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
