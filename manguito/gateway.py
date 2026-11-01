"""Pasarela local para modelos y un workspace de archivos de texto.

Sin dependencias de terceros. El servidor solo escucha en 127.0.0.1.
NO habilita shell, mouse, grabación ni acceso arbitrario al sistema.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

MAX_BYTES = 256 * 1024
PROPOSAL_TTL = 600
BLOCKED = {".git", ".ssh", ".venv", "venv", "node_modules", "__pycache__",
           ".env", ".env.local", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"}
BLOCKED_SUFFIXES = {".pem", ".key", ".pfx", ".p12"}


class AccessDenied(ValueError):
    pass


def safe_path(workspace: Path, name: str) -> Path:
    """Evita escapes del workspace, incluyendo enlaces simbólicos externos."""
    if not isinstance(name, str) or not name or "\x00" in name:
        raise AccessDenied("Nombre de ruta inválido")
    raw = Path(name)
    if raw.is_absolute() or raw.drive or ".." in raw.parts:
        raise AccessDenied("Solo se aceptan rutas relativas al workspace")
    for component in raw.parts:
        c = component.casefold()
        if c in BLOCKED or c.startswith(".env.") or Path(c).suffix in BLOCKED_SUFFIXES:
            raise AccessDenied("Ruta protegida")
    result = (workspace / raw).resolve()
    if not result.is_relative_to(workspace):
        raise AccessDenied("Ruta fuera del workspace")
    return result


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def request_json(url: str, payload: dict | None = None, timeout: int = 12) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"},
                  method="GET" if data is None else "POST")
    with urlopen(req, timeout=timeout) as response:
        answer = response.read(2 * 1024 * 1024 + 1)
    if len(answer) > 2 * 1024 * 1024:
        raise ValueError("La respuesta del proveedor es demasiado grande")
    return json.loads(answer)


class Manguito:
    def __init__(self, workspace: Path, token: str, model_url: str, writes=False):
        self.workspace = workspace.expanduser().resolve(strict=True)
        if not self.workspace.is_dir():
            raise ValueError("Workspace debe ser una carpeta")
        if not isinstance(token, str) or len(token) < 24:
            raise ValueError("MANGUITO_TOKEN requiere al menos 24 caracteres")
        parsed = urlparse(model_url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("URL del proveedor inválida")
        self.token = token
        self.model_url = model_url.rstrip("/")
        self.writes = bool(writes)
        self.approval_code = secrets.token_urlsafe(16)
        self.proposals = {}
        self.lock = threading.Lock()

    def authenticate(self, token: str) -> bool:
        return secrets.compare_digest(self.token, token)

    def status(self) -> dict:
        return {"name": "Manguito", "version": "0.1.0", "writes": self.writes,
                "localhost_only": True}

    def list_files(self, name=".") -> dict:
        folder = safe_path(self.workspace, name)
        if not folder.is_dir():
            raise ValueError("No es una carpeta")
        entries = []
        for item in sorted(folder.iterdir(), key=lambda p: p.name.casefold()):
            try:
                safe_path(self.workspace, str(item.relative_to(self.workspace)))
            except (AccessDenied, OSError):
                continue
            entries.append({"name": item.name, "directory": item.is_dir()})
            if len(entries) >= 200:
                break
        return {"path": name, "entries": entries, "limited": len(entries) == 200}

    def read_text(self, name: str) -> dict:
        path = safe_path(self.workspace, name)
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise ValueError("Solo archivos de texto de máximo 256 KiB")
        return {"path": name, "text": path.read_text(encoding="utf-8")}

    def propose(self, name: str, content: str) -> dict:
        if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_BYTES:
            raise ValueError("Texto inválido o mayor de 256 KiB")
        target = safe_path(self.workspace, name)
        if not target.parent.is_dir() or (target.exists() and not target.is_file()):
            raise ValueError("La carpeta debe existir")
        original = target.read_bytes() if target.exists() else b""
        if len(original) > MAX_BYTES:
            raise ValueError("Original demasiado grande")
        before = original.decode("utf-8")
        diff = "".join(difflib.unified_diff(
            before.splitlines(keepends=True), content.splitlines(keepends=True),
            fromfile="antes/" + name, tofile="despues/" + name))
        proposal_id = secrets.token_urlsafe(18)
        with self.lock:
            self.proposals[proposal_id] = {
                "path": name, "digest": sha256(original), "content": content.encode("utf-8"),
                "deadline": time.monotonic() + PROPOSAL_TTL}
        return {"proposal_id": proposal_id, "diff": diff, "expires_seconds": PROPOSAL_TTL,
                "local_approval_required": True}

    def apply(self, proposal_id: str, approval_code: str) -> dict:
        if not self.writes:
            raise AccessDenied("Escritura desactivada; habilítala localmente")
        if not isinstance(approval_code, str) or not secrets.compare_digest(
                self.approval_code, approval_code):
            raise AccessDenied("Falta la aprobación local")
        with self.lock:
            change = self.proposals.pop(proposal_id, None)
        if change is None or time.monotonic() > change["deadline"]:
            raise ValueError("Propuesta inexistente o vencida")
        target = safe_path(self.workspace, change["path"])
        existing = target.read_bytes() if target.exists() else b""
        if sha256(existing) != change["digest"]:
            raise ValueError("El archivo cambió; crea otra propuesta")
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode="wb", dir=target.parent, prefix=".manguito-", delete=False) as tmp:
                temp_name = tmp.name
                tmp.write(change["content"])
            os.replace(temp_name, target)
        finally:
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)
        return {"saved": True, "path": change["path"]}

    def models(self) -> dict:
        return request_json(self.model_url + "/models", timeout=5)

    def chat(self, messages: list, model: str | None = None) -> dict:
        if not isinstance(messages, list) or not 1 <= len(messages) <= 30:
            raise ValueError("Se requieren entre 1 y 30 mensajes")
        for message in messages:
            if (not isinstance(message, dict)
                    or message.get("role") not in ("system", "user", "assistant")
                    or not isinstance(message.get("content"), str)
                    or len(message["content"]) > 12000):
                raise ValueError("Mensajes inválidos: solo texto")
        if model is None:
            available = self.models().get("data", [])
            if not available:
                raise ValueError("No se encontró un modelo local")
            model = available[0]["id"]
        if not isinstance(model, str) or len(model) > 200:
            raise ValueError("Modelo inválido")
        answer = request_json(self.model_url + "/chat/completions", {
            "model": model, "messages": messages, "stream": False}, timeout=90)
        return {"model": answer.get("model", model),
                "text": answer["choices"][0]["message"].get("content", "")}


def make_handler(app: Manguito):
    class Handler(BaseHTTPRequestHandler):
        server_version = "ManguitoLocal/0.2"

        def log_message(self, format, *args):
            # En ejecutables sin consola (PyInstaller --windowed), stderr=None.
            # El logger predeterminado rompería las respuestas HTTP.
            return

        def respond(self, status: int, payload: dict):
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def invoke(self, method):
            try:
                self.respond(200, method())
            except AccessDenied as exc:
                self.respond(403, {"error": str(exc)})
            except (ValueError, KeyError, TypeError, IndexError, UnicodeError) as exc:
                self.respond(400, {"error": str(exc)})
            except (HTTPError, URLError, OSError, TimeoutError) as exc:
                self.respond(503, {"error": "Proveedor local inaccesible: " + type(exc).__name__})

        def allowed(self) -> bool:
            auth = self.headers.get("Authorization", "")
            if not auth.startswith("Bearer ") or not app.authenticate(auth[7:]):
                self.respond(401, {"error": "Token inválido"})
                return False
            return True

        def send_asset(self, filename: str, content_type: str):
            asset = Path(__file__).resolve().parent / "web" / filename
            try:
                raw = asset.read_bytes()
            except OSError:
                self.respond(404, {"error": "Recurso visual no disponible"})
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; script-src 'self'; style-src 'self'; "
                             "connect-src 'self'; img-src 'self' data:; "
                             "font-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            # Solo los tres recursos de interfaz son públicos; APIs requieren token.
            route = urlparse(self.path).path
            visual_assets = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/assets/style.css": ("style.css", "text/css; charset=utf-8"),
                "/assets/app.js": ("app.js", "text/javascript; charset=utf-8"),
            }
            if route in visual_assets:
                self.send_asset(*visual_assets[route])
                return
            if not self.allowed():
                return
            url = urlparse(self.path)
            path = parse_qs(url.query).get("path", ["."])[0]
            if url.path == "/v1/status":
                self.invoke(app.status)
            elif url.path == "/v1/models":
                self.invoke(app.models)
            elif url.path == "/v1/fs/list":
                self.invoke(lambda: app.list_files(path))
            elif url.path == "/v1/fs/read":
                self.invoke(lambda: app.read_text(path))
            else:
                self.respond(404, {"error": "Ruta desconocida"})

        def do_POST(self):
            if not self.allowed():
                return
            try:
                length = int(self.headers.get("Content-Length", "-1"))
                if length < 0 or length > MAX_BYTES:
                    raise ValueError("Solicitud ausente o mayor de 256 KiB")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Se requiere un objeto JSON")
            except (ValueError, UnicodeError) as exc:
                self.respond(400, {"error": str(exc)})
                return
            if self.path == "/v1/chat":
                self.invoke(lambda: app.chat(body.get("messages"), body.get("model")))
            elif self.path == "/v1/fs/propose":
                self.invoke(lambda: app.propose(body.get("path"), body.get("text")))
            elif self.path == "/v1/fs/apply":
                self.invoke(lambda: app.apply(body.get("proposal_id"),
                                              body.get("approval_code")))
            else:
                self.respond(404, {"error": "Ruta desconocida"})

    return Handler


def main():
    token = os.environ.get("MANGUITO_TOKEN", "")
    folder = Path(os.environ.get("MANGUITO_WORKSPACE", "."))
    endpoint = os.environ.get("MANGUITO_MODEL_URL", "http://127.0.0.1:1234/v1")
    writable = os.environ.get("MANGUITO_ENABLE_WRITES") == "1"
    app = Manguito(folder, token, endpoint, writes=writable)
    server = ThreadingHTTPServer(("127.0.0.1", 8765), make_handler(app))
    if sys.stdout is not None:
        print("Manguito disponible en http://127.0.0.1:8765", flush=True)
    if writable:
        if sys.stdout is not None:
            print("APROBACIÓN LOCAL DE ESCRITURA:", app.approval_code, flush=True)
            print("No compartas el código de aprobación con ninguna IA.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
