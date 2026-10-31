#!/usr/bin/env python3
"""Comparador SOLO LECTURA entre Matick Studio LM de Windows y GitHub.

Sin dependencias externas. No ejecuta scripts del proyecto ni copia archivos.
Por privacidad no registra secretos, rutas absolutas internas ni contenido.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

DEFAULT_LOCAL = r"C:\IA\Matick Studio LM"
DEFAULT_REPO = "DannMorlet/IA-Local-Cursor"
EXCLUDED_DIRS = {
    ".git", ".vs", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", "build", "out", "dist", "debug",
    "release", "bin", "obj", "models", "modelos", "weights", "pesos",
    "checkpoints", "cache", "caches", "backups", "respaldo", "respaldos",
    "privado", "private", "secrets", "secretos", "credentials",
    "capturas", "screenshots", "recordings", "grabaciones", "data",
}
PRIVATE_PARTS = {
    ".env", "token", "tokens", "password", "passwd", "credential",
    "credentials", "secret", "secrets", "apikey", "api_key", "keyfile",
    "private", "privado", "llave", "clave", "cookie", "session",
    "oauth", "authcache", "health", "salud",
}
SOURCE_SUFFIXES = {
    ".cpp", ".cc", ".c", ".h", ".hpp", ".cs", ".py", ".js", ".mjs",
    ".ts", ".tsx", ".jsx", ".json", ".md", ".txt", ".yml", ".yaml",
    ".toml", ".ini", ".ps1", ".html", ".css", ".rc", ".cmake",
    ".props", ".targets",
}
KNOWN_FILENAMES = {"cmakelists.txt", ".gitignore", "makefile", "dockerfile"}
MAX_FILES = 6000
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 32_000_000

FEATURES = {
    "Interfaz DirectX 12": (r"\bd3d12createdevice\b|[<\"]d3d12\.h[>\"]",),
    "Motor gráfico Vulkan": (r"\bvkcreateinstance\b|[<\"]vulkan/vulkan\.h[>\"]",),
    "MCP / JSON-RPC": (r"mcpservers|tools/list|tools/call",),
    "SDK lmstudio-js": (r"@lmstudio/sdk|LMStudioClient",),
    "API cloud HTTP": (r"ThreadingHTTPServer|FastAPI\(|\bexpress\(",),
    "Interfaz web": (r"react-dom|createRoot\(|<html",),
    "Mascota": (r"mascota|MascotProc|MatickMascot",),
}


def is_private(name: str) -> bool:
    name = name.casefold()
    if name.startswith(".env"):
        return True
    tokens = re.split(r"[^a-z0-9]+", name)
    return any(t in PRIVATE_PARTS for t in tokens)


def eligible(name: str) -> bool:
    return (name.casefold() in KNOWN_FILENAMES or Path(name).suffix.casefold() in SOURCE_SUFFIXES)


def git_blob_sha(raw: bytes) -> str:
    data = b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
    return hashlib.sha1(data).hexdigest()


def scan_local(root: Path) -> tuple[dict[str, dict], dict]:
    if not root.is_dir():
        raise FileNotFoundError(f"No existe la carpeta: {root}")
    seen: dict[str, dict] = {}
    mcp_configs = 0
    features = {key: False for key in FEATURES}
    skipped = 0
    total_bytes = 0
    for base, dirs, filenames in os.walk(root, topdown=True, followlinks=False):
        dirs[:] = [
            d for d in dirs
            if d.casefold() not in EXCLUDED_DIRS
            and not is_private(d)
            and not Path(base, d).is_symlink()
        ]
        for name in filenames:
            if len(seen) >= MAX_FILES:
                skipped += 1
                continue
            if name.casefold() == "mcp.json":
                mcp_configs += 1
                continue  # No leer ni publicar configuración real.
            if (name.casefold().endswith(".json") and not (
                name.casefold() in {"package.json", "tsconfig.json", "launch.json"}
                or name.casefold().endswith(".example.json")
            )):
                continue
            if not eligible(name) or is_private(name):
                continue
            item = Path(base, name)
            if item.is_symlink():
                continue
            try:
                length = item.stat().st_size
                if length > MAX_FILE_BYTES or total_bytes + length > MAX_TOTAL_BYTES:
                    skipped += 1
                    continue
                raw = item.read_bytes()
            except (OSError, PermissionError):
                skipped += 1
                continue
            total_bytes += len(raw)
            relative = item.relative_to(root).as_posix()
            # No se incluyen contenidos, incluso si un archivo válido contiene información privada.
            seen[relative] = {
                "sha": git_blob_sha(raw),
                "sha_lf": git_blob_sha(raw.replace(b"\r\n", b"\n")),
                "size": len(raw),
            }
            if item.suffix.casefold() in {".cpp", ".h", ".hpp", ".py", ".js", ".mjs", ".ts", ".tsx", ".cs"}:
                body = raw.decode("utf-8", errors="ignore")
                for label, patterns in FEATURES.items():
                    if not features[label] and any(re.search(p, body, re.IGNORECASE) for p in patterns):
                        features[label] = True
    return seen, {"detected": features, "skipped": skipped, "read_bytes": total_bytes, "mcp_configs": mcp_configs}


def github_tree(repo: str = DEFAULT_REPO, ref: str = "main") -> tuple[dict[str, dict], str]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("Repositorio inválido")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", ref):
        raise ValueError("Ref inválida. Usa main u otra rama simple")
    url = f"https://api.github.com/repos/{repo}/git/trees/{ref}?recursive=1"
    req = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "matick-comparador/0.1"})
    with urlopen(req, timeout=15) as response:
        payload = json.load(response)
    if payload.get("truncated"):
        raise ValueError("GitHub devolvió un árbol incompleto: comparación cancelada")
    entries = {}
    for entry in payload.get("tree", []):
        if entry.get("type") != "blob":
            continue
        path = entry["path"]
        parts = Path(path).parts
        if any(x.casefold() in EXCLUDED_DIRS or is_private(x) for x in parts):
            continue
        if not eligible(parts[-1]):
            continue
        entries[path] = {"sha": entry["sha"], "size": entry.get("size", 0)}
    return entries, payload["sha"]


def compare(local: dict, remote: dict) -> dict:
    a, b = set(local), set(remote)
    both = a & b
    same = sorted(p for p in both if local[p]["sha"] == remote[p]["sha"])
    eol_only = sorted(
        p for p in both
        if local[p]["sha"] != remote[p]["sha"] and local[p]["sha_lf"] == remote[p]["sha"]
    )
    different = sorted(both - set(same) - set(eol_only))
    return {
        "identicos": same,
        "solo_saltos_de_linea": eol_only,
        "diferentes": different,
        "solo_local": sorted(a - b),
        "solo_github": sorted(b - a),
    }


def markdown(root: Path, repo: str, ref: str, sha: str, files: dict, stats: dict, results: dict) -> str:
    def sample(items: list[str], n: int = 22) -> str:
        if not items:
            return "- Ninguno"
        text = "\n".join("- `" + x.replace("`", "") + "`" for x in items[:n])
        if len(items) > n:
            text += f"\n- ... y {len(items) - n} archivos más"
        return text
    lines = [
        "# Comparación Matick Studio LM: PC vs GitHub (solo lectura)",
        "",
        f"- Fecha UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- PC: `{root}`",
        f"- GitHub: `{repo}` / rama `{ref}` / árbol `{sha[:12]}`",
        f"- Archivos fuente examinados en PC: **{len(files)}**",
        f"- Archivos omitidos por tamaño/acceso/límites: **{stats['skipped']}**",
        "- Binarios, modelos, mcp.json y archivos de credenciales: **no leídos**",
        f"- Archivos mcp.json detectados por nombre (sin abrir): **{stats['mcp_configs']}**",
        "",
        "## Coincidencia de código por rutas relativas",
    ]
    for key, heading in [
        ("identicos", "Archivos idénticos"),
        ("solo_saltos_de_linea", "Solo cambia CRLF/LF"),
        ("diferentes", "Misma ruta, contenido diferente"),
        ("solo_local", "Solo en tu PC"),
        ("solo_github", "Solo en GitHub"),
    ]:
        lines.append(f"### {heading} ({len(results[key])})")
        if key != "identicos":
            lines.append(sample(results[key]))
        lines.append("")
    lines.extend(["## Funciones detectadas en el código local"])
    for feature, present in stats["detected"].items():
        lines.append(f"- {feature}: {'se encontró código relacionado' if present else 'no se detectó en el muestreo'}")
    lines.extend([
        "",
        "## Recomendación de integración",
        "1. Conservar ambas carpetas y respaldos sin sobrescribir nada.",
        "2. Revisar primero los archivos exclusivos del PC y los de contenido diferente.",
        "3. Transferir cambios mediante una rama/PR y ejecutar pruebas automáticas.",
        "4. Validar la interfaz DirectX 12 y mascota en Windows antes de distribuir el EXE.",
        "",
        "_Este informe nunca demuestra que un módulo se haya ejecutado: solo compara archivos y detecta patrones de código._",
    ])
    return "\n".join(lines).replace("\n", "\n") + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Comparación segura Matick Studio LM PC / GitHub")
    parser.add_argument("--local", default=DEFAULT_LOCAL, help="Carpeta Matick Studio LM en Windows")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--ref", default="main")
    parser.add_argument("--output", help="Opcional: guardar reporte FUERA de la carpeta del proyecto")
    args = parser.parse_args()
    local_path = Path(args.local).expanduser().resolve()
    try:
        local, stats = scan_local(local_path)
        remote, sha = github_tree(args.repo, args.ref)
        diff = compare(local, remote)
        report = markdown(local_path, args.repo, args.ref, sha, local, stats, diff)
        if args.output:
            target = Path(args.output).expanduser().resolve()
            if target == local_path or local_path in target.parents:
                raise ValueError("El reporte debe guardarse FUERA del proyecto local")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(report, encoding="utf-8")
            print(f"Reporte guardado en: {target}")
        else:
            print(report)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
