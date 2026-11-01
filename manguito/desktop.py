"""Lanzador de Manguito Studio independiente del Manguito.exe original."""
from __future__ import annotations

import os
from pathlib import Path
import secrets
from threading import Timer
import webbrowser

from manguito.gateway import main as run_gateway


def main():
    workspace = Path(os.environ.get("MANGUITO_WORKSPACE", str(Path.home() / "ManguitoWorkspace")))
    workspace.mkdir(parents=True, exist_ok=True)
    os.environ["MANGUITO_WORKSPACE"] = str(workspace)
    if not os.environ.get("MANGUITO_TOKEN"):
        os.environ["MANGUITO_TOKEN"] = secrets.token_urlsafe(32)
    url = "http://127.0.0.1:8765/"
    print("=" * 54, flush=True)
    print("MANGUITO STUDIO · PREVIEW", flush=True)
    print("=" * 54, flush=True)
    print("Abriendo:", url, flush=True)
    print("Carpeta permitida:", workspace, flush=True)
    print("Token de ESTA SESIÓN (no compartir):", flush=True)
    print(os.environ["MANGUITO_TOKEN"], flush=True)
    print("Pégalo en la pantalla Conectar Manguito.", flush=True)
    print("Para cerrar el servidor: Ctrl + C", flush=True)
    print("=" * 54, flush=True)
    launch = Timer(1.25, lambda: webbrowser.open(url))
    launch.daemon = True
    launch.start()
    run_gateway()


if __name__ == "__main__":
    main()
