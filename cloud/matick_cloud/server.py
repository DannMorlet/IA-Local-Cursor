"""Servidor HTTP minimalista de Matick Studio LM Cloud.

Sin dependencias externas. El servidor es un prototipo para una sola instancia:
requiere un proxy TLS y controles adicionales antes de exponerse a internet.
"""
from __future__ import annotations

import hmac
import json
import os
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sqlite3
from typing import Any
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .provider import OpenAICompatibleProvider, ProviderResponseError, ProviderUnavailable

ROLES = frozenset({
    "matick-studio-lm", "chatgpt", "matick-chat", "matick-codex",
    "matick-reloj", "alexa", "windows-dx12",
})
MAX_BYTES = 16 * 1024
MAX_EVENTS = 100


class EventStore:
    """Eventos persistentes y aislados por buzón del destinatario."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS events ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "created_at TEXT NOT NULL,"
                "source TEXT NOT NULL,"
                "target TEXT NOT NULL,"
                "kind TEXT NOT NULL,"
                "payload TEXT NOT NULL)"
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_target_id "
                "ON events(target, id)"
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def publish(self, source: str, target: str, kind: str, payload: dict[str, Any]) -> int:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as db:
            result = db.execute(
                "INSERT INTO events(created_at,source,target,kind,payload) "
                "VALUES(?,?,?,?,?)",
                (now, source, target, kind, json.dumps(payload, ensure_ascii=False)),
            )
            return int(result.lastrowid)

    def inbox(self, actor: str, after: int, limit: int) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT id,created_at,source,target,kind,payload "
                "FROM events WHERE target=? AND id>? ORDER BY id LIMIT ?",
                (actor, after, limit),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "source": row["source"],
                "target": row["target"],
                "kind": row["kind"],
                "payload": json.loads(row["payload"]),
            }
            for row in rows
        ]


def load_tokens(value: str) -> dict[str, str]:
    """Una credencial distinta por componente; fallar si el entorno es inseguro."""
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("MATICK_TOKENS_JSON no es JSON válido") from exc
    if not isinstance(parsed, dict) or not parsed:
        raise ValueError("MATICK_TOKENS_JSON debe contener al menos un rol")
    if any(
        role not in ROLES or not isinstance(token, str) or len(token) < 16
        for role, token in parsed.items()
    ):
        raise ValueError("Los roles deben ser conocidos y los tokens tener al menos 16 caracteres")
    if len(set(parsed.values())) != len(parsed):
        raise ValueError("No se permite reutilizar un token en varios roles")
    return parsed


class MatickHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        store: EventStore,
        tokens: dict[str, str],
        provider: OpenAICompatibleProvider | None = None,
    ) -> None:
        self.store = store
        self.tokens = tokens.copy()
        self.provider = provider if provider is not None else OpenAICompatibleProvider.from_env()
        super().__init__(address, MatickHandler)


class MatickHandler(BaseHTTPRequestHandler):
    server: MatickHTTPServer
    server_version = "MatickStudioLMCloud/" + __version__

    def _respond(self, status: int | HTTPStatus, data: dict[str, Any]) -> None:
        encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _respond_text(self, status: int | HTTPStatus, content: str) -> None:
        encoded = content.encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _actor(self) -> str | None:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            self._respond(HTTPStatus.UNAUTHORIZED, {"error": "Bearer token requerido"})
            return None
        supplied = auth[7:]
        for role, secret in self.server.tokens.items():
            if hmac.compare_digest(supplied, secret):
                return role
        self._respond(HTTPStatus.UNAUTHORIZED, {"error": "Token inválido"})
        return None

    def do_GET(self) -> None:
        route = urlsplit(self.path)
        if route.path == "/health":
            self._respond(HTTPStatus.OK, {"service": "matick-studio-lm-cloud", "version": __version__, "status": "ok"})
            return

        if route.path not in {"/v1/status", "/v1/events", "/v1/capabilities"}:
            self._respond(HTTPStatus.NOT_FOUND, {"error": "Ruta no encontrada"})
            return

        actor = self._actor()
        if actor is None:
            return
        if route.path == "/v1/status":
            self._respond(HTTPStatus.OK, {
                "service": "matick-studio-lm-cloud",
                "actor": actor,
                "transport": "http-polling",
                "storage": "sqlite",
            })
            return

        if route.path == "/v1/capabilities":
            self._respond(HTTPStatus.OK, {
                "actor": actor,
                "chat": {"configured": self.server.provider.configured},
                "events": {"configured": True},
                "mcp": {"configured": False, "reason": "ToolHub funciona separado del servidor cloud"},
                "devices": {"configured": False},
                "cloud_model": self.server.provider.model if self.server.provider.configured else None,
            })
            return

        args = parse_qs(route.query)
        try:
            after = int(args.get("after", ["0"])[0])
            limit = int(args.get("limit", ["50"])[0])
        except (ValueError, TypeError):
            self._respond(HTTPStatus.BAD_REQUEST, {"error": "after y limit deben ser números enteros"})
            return
        if after < 0 or not 1 <= limit <= MAX_EVENTS:
            self._respond(HTTPStatus.BAD_REQUEST, {"error": "Rango incorrecto"})
            return
        events = self.server.store.inbox(actor, after, limit)
        self._respond(HTTPStatus.OK, {"actor": actor, "events": events})

    def do_POST(self) -> None:
        route = urlsplit(self.path).path
        if route not in {"/v1/events", "/v1/chat"}:
            self._respond(HTTPStatus.NOT_FOUND, {"error": "Ruta no encontrada"})
            return
        actor = self._actor()
        if actor is None:
            return

        try:
            size = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            self._respond(HTTPStatus.BAD_REQUEST, {"error": "Content-Length inválido"})
            return
        if size < 1 or size > MAX_BYTES:
            self._respond(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "Tamaño inválido o superior a 16 KiB"})
            return
        try:
            data = json.loads(self.rfile.read(size))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._respond(HTTPStatus.BAD_REQUEST, {"error": "JSON inválido"})
            return

        if not isinstance(data, dict):
            self._respond(HTTPStatus.BAD_REQUEST, {"error": "Se espera un objeto JSON"})
            return
        if route == "/v1/chat":
            messages = data.get("messages")
            if not isinstance(messages, list) or not 1 <= len(messages) <= 12 or not all(
                isinstance(m, dict)
                and set(m) == {"role", "content"}
                and m["role"] in ("user", "assistant")
                and isinstance(m["content"], str)
                and 1 <= len(m["content"]) <= 8000
                for m in messages
            ) or sum(len(m["content"]) for m in messages if isinstance(m, dict)
                     and isinstance(m.get("content"), str)) > 12000:
                self._respond(HTTPStatus.BAD_REQUEST, {
                    "error": "messages debe contener 1..12 mensajes user/assistant, texto máximo 12k",
                })
                return
            if messages[-1]["role"] != "user":
                self._respond(HTTPStatus.BAD_REQUEST, {"error": "Último mensaje debe ser del usuario"})
                return
            try:
                result = self.server.provider.respond(messages)
            except ProviderUnavailable as exc:
                self._respond(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(exc)})
                return
            except ProviderResponseError as exc:
                self._respond(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
                return
            if "text/plain" in self.headers.get("Accept", ""):
                self._respond_text(HTTPStatus.OK, result["content"])
            else:
                self._respond(HTTPStatus.OK, result)
            return

        target = data.get("target")
        kind = data.get("kind")
        payload = data.get("payload")
        if not isinstance(target, str) or target not in ROLES or not isinstance(kind, str) or not 1 <= len(kind) <= 64 or not isinstance(payload, dict):
            self._respond(HTTPStatus.BAD_REQUEST, {"error": "target, kind o payload inválidos"})
            return
        if any(ord(c) < 32 for c in kind):
            self._respond(HTTPStatus.BAD_REQUEST, {"error": "kind contiene caracteres de control"})
            return

        event_id = self.server.store.publish(actor, target, kind, payload)
        self._respond(HTTPStatus.CREATED, {"id": event_id, "source": actor, "target": target})

    def log_message(self, format: str, *args: Any) -> None:
        # Log mínimo. Nunca imprimir cabeceras Authorization ni payloads.
        print("%s - %s" % (self.address_string(), format % args), flush=True)


def main() -> None:
    tokens = load_tokens(os.environ.get("MATICK_TOKENS_JSON", ""))
    host = os.environ.get("MATICK_HOST", "127.0.0.1")
    port = int(os.environ.get("MATICK_PORT", "8787"))
    db_path = os.environ.get("MATICK_DB_PATH", "./matick-events.db")
    server = MatickHTTPServer((host, port), EventStore(db_path), tokens)
    print("Matick Studio LM Cloud %s escuchando en %s:%d" % (__version__, host, port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Servidor detenido")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
