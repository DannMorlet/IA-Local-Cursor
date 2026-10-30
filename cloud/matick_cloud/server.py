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

ROLES = frozenset({
    "matick-studio-lm", "chatgpt", "matick-chat", "matick-codex",
    "matick-reloj", "alexa", "windows-dx12", "matick-pet",
})
MAX_BYTES = 16 * 1024
MAX_EVENTS = 100
MAX_FANOUT = 7

# Studio and ChatGPT may route work to any connected service. Other clients
# report to Studio and ChatGPT; the Work pet is a read-only status surface.
ROUTE_TARGETS = {
    "matick-studio-lm": ROLES - {"matick-studio-lm"},
    "chatgpt": ROLES - {"chatgpt", "matick-pet"},
    "matick-chat": frozenset({"matick-studio-lm", "chatgpt"}),
    "matick-codex": frozenset({"matick-studio-lm", "chatgpt"}),
    "matick-reloj": frozenset({"matick-studio-lm", "chatgpt"}),
    "alexa": frozenset({"matick-studio-lm", "chatgpt"}),
    "windows-dx12": frozenset({"matick-studio-lm", "chatgpt"}),
    "matick-pet": frozenset(),
}
DIRECTORS = frozenset({"matick-studio-lm", "chatgpt"})
STATUS_STATES = frozenset({"idle", "working", "waiting", "error", "offline"})
STATUS_FIELDS = frozenset({"component", "state", "updated_at", "progress_pct"})


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

    def publish_many(
        self, source: str, targets: list[str], kind: str, payload: dict[str, Any]
    ) -> list[int]:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        ids: list[int] = []
        with self._connect() as db:
            for target in targets:
                result = db.execute(
                    "INSERT INTO events(created_at,source,target,kind,payload) "
                    "VALUES(?,?,?,?,?)",
                    (now, source, target, kind, json.dumps(payload, ensure_ascii=False)),
                )
                ids.append(int(result.lastrowid))
        return ids

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
    ) -> None:
        self.store = store
        self.tokens = tokens.copy()
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

        if route.path not in {"/v1/status", "/v1/routes", "/v1/events"}:
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

        if route.path == "/v1/routes":
            self._respond(HTTPStatus.OK, {
                "actor": actor,
                "allowed_targets": sorted(ROUTE_TARGETS[actor]),
                "can_fanout": actor in DIRECTORS,
                "pet_status_only": actor == "matick-studio-lm",
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
        path = urlsplit(self.path).path
        if path not in {"/v1/events", "/v1/direct"}:
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
        kind = data.get("kind")
        payload = data.get("payload")
        if not isinstance(kind, str) or not 1 <= len(kind) <= 64 or not isinstance(payload, dict):
            self._respond(HTTPStatus.BAD_REQUEST, {"error": "kind o payload inválidos"})
            return
        if any(ord(c) < 32 for c in kind):
            self._respond(HTTPStatus.BAD_REQUEST, {"error": "kind contiene caracteres de control"})
            return
        if kind == "status.snapshot" and actor != "matick-studio-lm":
            self._respond(HTTPStatus.FORBIDDEN, {"error": "solo Matick Studio puede publicar status.snapshot"})
            return
        if kind == "status.snapshot":
            component = payload.get("component")
            state = payload.get("state")
            updated_at = payload.get("updated_at")
            progress = payload.get("progress_pct")
            try:
                parsed_time = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except (AttributeError, TypeError, ValueError):
                parsed_time = None
            if (set(payload) - STATUS_FIELDS or not isinstance(component, str)
                    or component not in ROLES - {"matick-pet"}
                    or not isinstance(state, str) or state not in STATUS_STATES
                    or parsed_time is None
                    or parsed_time.tzinfo is None
                    or (progress is not None and
                        (isinstance(progress, bool) or not isinstance(progress, int)
                         or not 0 <= progress <= 100))):
                self._respond(HTTPStatus.BAD_REQUEST, {
                    "error": "status.snapshot requiere component, state, updated_at UTC y progress_pct opcional (0-100)"
                })
                return

        if path == "/v1/direct":
            if actor not in DIRECTORS:
                self._respond(HTTPStatus.FORBIDDEN, {"error": "rol sin permiso de dirección"})
                return
            targets = data.get("targets")
            if (not isinstance(targets, list) or not 1 <= len(targets) <= MAX_FANOUT
                    or any(not isinstance(target, str) for target in targets)
                    or len(set(targets)) != len(targets)):
                self._respond(HTTPStatus.BAD_REQUEST, {"error": "targets debe ser una lista única de 1 a 7 roles"})
                return
        else:
            target = data.get("target")
            if not isinstance(target, str):
                self._respond(HTTPStatus.BAD_REQUEST, {"error": "target inválido"})
                return
            targets = [target]

        if any(target not in ROLES or target == actor for target in targets):
            self._respond(HTTPStatus.BAD_REQUEST, {"error": "target desconocido o igual al emisor"})
            return
        forbidden = [target for target in targets if target not in ROUTE_TARGETS[actor]]
        if forbidden:
            self._respond(HTTPStatus.FORBIDDEN, {
                "error": "ruta no permitida para este rol",
                "targets": forbidden,
            })
            return
        if "matick-pet" in targets and kind != "status.snapshot":
            self._respond(HTTPStatus.FORBIDDEN, {"error": "Matick Pet solo recibe status.snapshot"})
            return

        ids = self.server.store.publish_many(actor, targets, kind, payload)
        if path == "/v1/direct":
            self._respond(HTTPStatus.CREATED, {
                "source": actor,
                "kind": kind,
                "deliveries": [
                    {"id": event_id, "target": target}
                    for event_id, target in zip(ids, targets)
                ],
            })
        else:
            self._respond(HTTPStatus.CREATED, {
                "id": ids[0], "source": actor, "target": targets[0],
            })

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

