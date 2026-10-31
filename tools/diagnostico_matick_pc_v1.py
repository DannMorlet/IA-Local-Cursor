#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Matick Studio LM: inventario local y diagnostico de preparacion 1-100.

Solo lee por defecto. No modifica programas ni envia datos.
Los resultados se guardan FUERA del proyecto, en Descargas.
Opciones --red y --pruebas requieren solicitud explicita.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_ROOT = r"C:\IA\Matick Studio LM"
VENDOR_DIRS = {"cuda", "third_party", "third-party", "node_modules", ".venv",
               "venv", "vendor", "external", ".git", "models", "modelos",
               "weights", "checkpoints", "build", "dist", ".vs"}
SENSITIVE = {"mcp.json", "password", "token", "secret", "apikey", "api_key", "credentials",
             "private", "privado", "cookie", ".env", "health", "salud"}
REQUIRED = ["README.md", "windows/src/main.cpp",
            "cloud/matick_cloud/server.py", "cloud/matick_cloud/models.py",
            "cloud/matick_cloud/tasks.py", "cloud/matick_cloud/web/index.html",
            "cloud/matick_cloud/web/app.js", "cloud/matick_cloud/web/style.css"]
WEIGHTS = {"directorio": 8, "inventario": 8, "estructura": 10,
           "ejecutable": 10, "formato_pe": 7, "python_sintaxis": 12,
           "json_sintaxis": 6, "panel_web": 8, "manifiesto": 10,
           "tests": 9, "api": 6, "rest_modelos": 6}


def safe_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def sensitive_path(relative: str) -> bool:
    parts = relative.lower().replace("\\", "/").split("/")
    return any(
        p.startswith(".env") or any(term in p for term in SENSITIVE)
        for p in parts
    )


def vendor_path(relative: str) -> bool:
    return any(p.casefold() in VENDOR_DIRS for p in relative.replace("\\", "/").split("/"))


def make_check(key: str, ok: bool | None, detail: str) -> dict:
    return {"nombre": key, "peso": WEIGHTS[key],
            "estado": "OK" if ok is True else ("FALLA" if ok is False else "SIN_PROBAR"),
            "puntos": WEIGHTS[key] if ok is True else 0, "detalle": detail}


def scan(root: Path):
    inventory = []
    errors = []
    folders = 0
    for base, dirs, files in os.walk(root, topdown=True, followlinks=False):
        # Contar incluso bibliotecas pesadas, pero jamas seguir enlaces/junctions.
        clean = []
        for dirname in dirs:
            child = Path(base) / dirname
            if child.is_symlink() or (hasattr(child, "is_junction") and child.is_junction()):
                continue
            clean.append(dirname)
        dirs[:] = clean
        folders += 1
        for filename in files:
            path = Path(base) / filename
            if path.is_symlink():
                continue
            try:
                info = path.stat()
                rel = safe_rel(path, root)
                inventory.append({
                    "ruta": rel, "bytes": info.st_size,
                    "extension": path.suffix.casefold() or "(sin extension)",
                    "tercero_o_pesado": vendor_path(rel),
                    "sensible": sensitive_path(rel),
                })
            except OSError as exc:
                errors.append(f"Archivo inaccesible: {type(exc).__name__}")
    return inventory, folders, errors


def syntax_checks(root: Path, inventory: list[dict]):
    py_count = 0
    py_error = []
    json_count = 0
    json_error = []
    node_checks = []
    for entry in inventory:
        rel = entry["ruta"]
        if entry["tercero_o_pesado"] or entry["sensible"] or entry["bytes"] > 2_000_000:
            continue
        path = root / rel
        if path.suffix.casefold() == ".py" and py_count < 2000:
            py_count += 1
            try:
                # Compilar AST no ejecuta imports, scripts ni modelos.
                ast.parse(path.read_bytes(), filename=rel)
            except (SyntaxError, ValueError, OSError, UnicodeDecodeError) as exc:
                py_error.append(f"{rel}: {type(exc).__name__}")
        if path.suffix.casefold() == ".json" and (
            path.name in {"package.json", "tsconfig.json", "manifest.json"}
            or path.name.endswith(".example.json")
        ):
            json_count += 1
            try:
                json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeDecodeError, ValueError) as exc:
                json_error.append(f"{rel}: {type(exc).__name__}")
    app_js = root / "cloud/matick_cloud/web/app.js"
    if app_js.is_file() and shutil.which("node"):
        try:
            result = subprocess.run(["node", "--check", str(app_js)], capture_output=True,
                                    text=True, timeout=15, shell=False)
            node_checks.append({"archivo": "app.js", "ok": result.returncode == 0})
        except (OSError, subprocess.TimeoutExpired):
            node_checks.append({"archivo": "app.js", "ok": False})
    return py_count, py_error, json_count, json_error, node_checks


def check_manifest(root: Path):
    path = root / "manifest.json"
    if not path.is_file():
        return None, "Sin manifest.json; integridad de paquete no comprobada"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        items = data.get("files")
        if not isinstance(items, list) or not items:
            raise ValueError("Lista files no disponible")
        verified = 0
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Entrada invalida")
            rel = item.get("path", "")
            if not isinstance(rel, str) or not rel or "\\" in rel or ":" in rel:
                raise ValueError("Ruta insegura en manifest")
            target = (root / rel).resolve()
            if not target.is_relative_to(root) or not target.is_file() or target.is_symlink():
                raise ValueError("Archivo faltante o ruta fuera del proyecto")
            expected = item.get("sha256", "")
            if not isinstance(expected, str) or len(expected) != 64:
                raise ValueError("Hash no valido")
            sha = hashlib.sha256()
            with target.open("rb") as handle:
                for piece in iter(lambda: handle.read(1024 * 1024), b""):
                    sha.update(piece)
            if sha.hexdigest().lower() != expected.lower():
                raise ValueError("SHA256 diferente")
            verified += 1
        return True, f"{verified} archivos coinciden con SHA256 del paquete"
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return False, f"Integridad fallida: {type(exc).__name__} ({str(exc)[:90]})"


def network_probe(url):
    try:
        # Solo localhost/loopback, GET sin token y sin ejecutar motores.
        with urlopen(Request(url, headers={"User-Agent": "MatickDiagnostic/1.0"}),
                     timeout=3) as resp:
            raw = resp.read(60_000)
            data = json.loads(raw)
            return resp.status == 200 and isinstance(data, dict), "Respuesta HTTP 200 JSON"
    except HTTPError as exc:
        if exc.code in (401, 403):
            return None, "Servidor responde pero requiere autenticacion (no se solicitan secretos)"
        return False, f"HTTP {exc.code}"
    except (OSError, URLError, ValueError, TimeoutError) as exc:
        return False, f"No responde: {type(exc).__name__}"


def run_project_tests(root: Path):
    tests = root / "cloud/tests"
    if not tests.is_dir():
        return None, "No existe cloud/tests"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "cloud")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", str(tests), "-v"],
            cwd=str(root), env=env, capture_output=True, text=True,
            shell=False, timeout=90,
        )
        summary = "\n".join((result.stderr + "\n" + result.stdout).splitlines()[-12:])
        return result.returncode == 0, summary[:1300]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"Pruebas abortadas: {type(exc).__name__}"


def diagnose(root: Path, *, tests=False, network=False):
    if not root.is_dir():
        raise FileNotFoundError(f"No existe el proyecto: {root}")
    inventory, folders, errors = scan(root)
    py_count, py_errors, json_count, json_errors, node_checks = syntax_checks(root, inventory)
    exe_candidates = [x for x in inventory if x["ruta"].lower().endswith("matickstudiolm.exe")]
    if not exe_candidates:
        exe_candidates = [x for x in inventory if x["extension"] == ".exe"
                          and not x["tercero_o_pesado"]][:10]
    pe_ok = False
    pe_attempted = False
    for item in exe_candidates[:10]:
        try:
            with (root / item["ruta"]).open("rb") as handle:
                pe_ok = handle.read(2) == b"MZ"
            pe_attempted = True
            if pe_ok:
                break
        except OSError:
            pe_attempted = True
    required_count = sum((root / p).is_file() for p in REQUIRED)
    web_count = sum((root / p).is_file() for p in REQUIRED[-3:])
    manifest_ok, manifest_info = check_manifest(root)
    test_ok, test_info = run_project_tests(root) if tests else (
        None, "No ejecutadas; activa --pruebas para ejecutar SOLO tests propios en tu PC"
    )
    api_ok, api_info = network_probe("http://127.0.0.1:8787/health") if network else (
        None, "No comprobado; activa --red"
    )
    models_ok, models_info = network_probe("http://127.0.0.1:1234/api/v1/models") if network else (
        None, "No comprobado; activa --red"
    )
    checks = [
        make_check("directorio", True, "Ruta local accesible"),
        make_check("inventario", bool(inventory) and not errors,
                   f"{len(inventory)} archivos, {folders} carpetas, {len(errors)} errores"),
        make_check("estructura", required_count == len(REQUIRED),
                   f"{required_count}/{len(REQUIRED)} componentes esperados de Matick Cloud v1"),
        make_check("ejecutable", bool(exe_candidates), f"{len(exe_candidates)} EXE candidatos"),
        make_check("formato_pe", pe_ok if pe_attempted else None,
                   "Encabezado PE/MZ detectado (no significa que el EXE funcione)"),
        make_check("python_sintaxis", py_count > 0 and not py_errors,
                   f"{py_count} scripts Python analizados; {len(py_errors)} errores"),
        make_check("json_sintaxis", not json_errors if json_count else None,
                   f"{json_count} JSON seguros examinados; {len(json_errors)} errores"),
        make_check("panel_web", web_count == 3 and all(x["ok"] for x in node_checks),
                   f"{web_count}/3 recursos web; node --check: {node_checks or 'no disponible'}"),
        make_check("manifiesto", manifest_ok, manifest_info),
        make_check("tests", test_ok, test_info),
        make_check("api", api_ok, api_info),
        make_check("rest_modelos", models_ok, models_info),
    ]
    score = max(1, min(100, sum(x["puntos"] for x in checks)))
    checked = sum(x["peso"] for x in checks if x["estado"] != "SIN_PROBAR")
    return {
        "version_diagnostico": "1.0", "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "raiz": str(root), "puntaje_preparacion": score,
        "cobertura_verificacion_pct": checked,
        "advertencia": "El puntaje NO demuestra un porcentaje real de funcionalidad ni valida DirectX 12 en uso.",
        "resumen": {
            "archivos_totales": len(inventory),
            "carpetas_totales": folders,
            "gigabytes_referenciados": round(sum(x["bytes"] for x in inventory) / (1024**3), 3),
            "terceros_o_pesados": sum(x["tercero_o_pesado"] for x in inventory),
            "archivos_sensibles_no_leidos": sum(x["sensible"] for x in inventory),
            "sintaxis_python_analizados": py_count, "errores_python": py_errors[:40],
            "errores_json": json_errors[:40],
            "errores_lectura": errors[:20],
            "extensiones": Counter(x["extension"] for x in inventory).most_common(18),
        },
        "checks": checks,
    }, inventory


def write_report(report: dict, inventory: list[dict], destination: Path, root: Path):
    destination = destination.resolve()
    if destination == root or root in destination.parents:
        raise ValueError("La salida debe estar FUERA del proyecto local")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "Matick_Diagnostico_Resumen.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    # Inventario completo LOCAL, contiene nombres de archivos: revisar antes de compartir.
    (destination / "Matick_Inventario_Completo.json").write_text(
        json.dumps(inventory, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Matick Studio LM · diagnóstico de MORLET-GAMING",
        "", f"Fecha: {report['fecha_utc']}",
        f"Carpeta: \`{report['raiz']}\`", "",
        f"## Preparación comprobada: {report['puntaje_preparacion']}/100",
        f"Cobertura de comprobaciones: **{report['cobertura_verificacion_pct']}%**",
        "",
        "> Este valor **no equivale** a que el programa funcione en ese porcentaje. "
        "Las pruebas omitidas o no ejecutadas NO se consideran aprobadas.",
        "",
        "## Resultados", "",
        "| Comprobación | Peso | Resultado | Evidencia |",
        "| --- | ---: | --- | --- |",
    ]
    for test in report["checks"]:
        detail = str(test["detalle"]).replace("|", "/").replace("\n", " ")
        lines.append(f"| {test['nombre']} | {test['peso']} | {test['estado']} | {detail[:180]} |")
    s = report["resumen"]
    lines += ["", "## Inventario total", "",
        f"- Archivos encontrados: **{s['archivos_totales']}**",
        f"- Carpetas: **{s['carpetas_totales']}**",
        f"- Tamaño referenciado: **{s['gigabytes_referenciados']} GiB**",
        f"- Archivos en carpetas de terceros/modelos: **{s['terceros_o_pesados']}**",
        f"- Archivos sensibles contados, sin abrir su contenido: **{s['archivos_sensibles_no_leidos']}**",
        "", "## Qué falta para probar funcionalidad real",
        "1. Abrir MatickStudioLM.exe manualmente y revisar DirectX 12, mascota y controles.",
        "2. Activar un proveedor de modelos y enviar un chat para verificar inferencia.",
        "3. Comprobar carga y descarga de modelos con RAM/VRAM medidas.",
        "4. Si es seguro ejecutar pruebas propias, repetir con --pruebas.",
        "5. Revisar MCP, ChatGPT, Alexa y reloj individualmente; no se dan por integrados.",
        "",
        "**Privacidad:** el inventario completo contiene nombres de archivos; "
        "no compartas Matick_Inventario_Completo.json sin revisarlo.",
        "",
    ]
    path = destination / "Matick_Diagnostico_Informe.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description="Matick: diagnóstico de archivos y preparación 1-100")
    parser.add_argument("--ruta", default=DEFAULT_ROOT, help="Ruta del proyecto Matick")
    parser.add_argument("--salida", default=str(Path.home() / "Downloads" / "Matick_Diagnostico_PC"))
    parser.add_argument("--red", action="store_true", help="Solo GET localhost:8787 y localhost:1234")
    parser.add_argument("--pruebas", action="store_true",
                        help="AVISO: ejecuta código de tests propio del proyecto, solo con autorización")
    args = parser.parse_args()
    root = Path(args.ruta).expanduser().resolve()
    if not root.is_dir():
        parser.error("No existe el directorio del proyecto: " + str(root))
    report, inventory = diagnose(root, tests=args.pruebas, network=args.red)
    result = write_report(report, inventory, Path(args.salida).expanduser(), root)
    print(f"Preparación observada: {report['puntaje_preparacion']}/100 "
          f"| cobertura: {report['cobertura_verificacion_pct']}%")
    print("Reporte:", result)
    print("No se ejecutó ni modificó el EXE, ni se envió información a la nube.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
