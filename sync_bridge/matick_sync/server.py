"""Matick Sync Bridge: long-polling inmediato, SQLite y API de modelos optativa.

Por defecto escucha SOLO en 127.0.0.1. No expone puertos a internet.
"""
from __future__ import annotations

import hmac
from contextlib import closing
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from . import __version__
from . import providers

ROLES = frozenset({'morlet', 'matick', 'chatgpt', 'gemini', 'claude'})
DESTINATIONS = ROLES | {'all'}
MAX_BODY = 8192
MAX_TEXT = 6000
MAX_POLL = 20


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def load_tokens() -> dict[str, str]:
    """Una clave por rol, o una clave local para Morlet."""
    raw = os.getenv('MATICK_SYNC_TOKENS_JSON')
    if raw:
        try:
            tokens = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError('MATICK_SYNC_TOKENS_JSON no es JSON válido') from e
    else:
        key = os.getenv('MATICK_SYNC_TOKEN', '')
        tokens = {'morlet': key}
    if (not isinstance(tokens, dict) or not tokens or
        any(k not in ROLES or not isinstance(v, str) or len(v) < 20
            for k, v in tokens.items()) or
        len(set(tokens.values())) != len(tokens)):
        raise ValueError('Se requieren tokens únicos de al menos 20 caracteres por rol')
    return tokens


def default_db() -> Path:
    root = Path(os.getenv('LOCALAPPDATA') or Path.home() / '.matick') / 'MatickSyncBridge'
    return root / 'events.db'


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.changed = threading.Condition()
        with closing(self.db()) as conn, conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    at TEXT NOT NULL, source TEXT NOT NULL, recipient TEXT NOT NULL,
                    kind TEXT NOT NULL, text TEXT NOT NULL, client_id TEXT,
                    UNIQUE(source, client_id)
                );
                CREATE INDEX IF NOT EXISTS idx_events_id ON events(id);
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, at TEXT NOT NULL, status TEXT NOT NULL,
                    prompt TEXT NOT NULL, agents TEXT NOT NULL, result TEXT NOT NULL
                );
            ''')
            conn.execute("UPDATE tasks SET status='interrupted' "
                         "WHERE status IN ('queued','running')")

    def db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=8)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA busy_timeout=8000')
        return conn

    def publish(self, source: str, recipient: str, kind: str, text: str,
                client_id: str | None = None) -> int:
        with closing(self.db()) as conn, conn:
            if client_id:
                existing = conn.execute(
                    'SELECT id FROM events WHERE source=? AND client_id=?',
                    (source, client_id)).fetchone()
                if existing:
                    return int(existing['id'])
            try:
                cur = conn.execute(
                    'INSERT INTO events(at,source,recipient,kind,text,client_id) '
                    'VALUES(?,?,?,?,?,?)', (now(), source, recipient, kind, text, client_id))
                event_id = int(cur.lastrowid)
            except sqlite3.IntegrityError:
                # Llamadas concurrentes con la misma clave de idempotencia.
                found = conn.execute(
                    'SELECT id FROM events WHERE source=? AND client_id=?',
                    (source, client_id)).fetchone()
                if not found:
                    raise
                return int(found['id'])
        with self.changed:
            self.changed.notify_all()
        return event_id

    def list_events(self, actor: str, after: int, limit: int = 50) -> list[dict]:
        with closing(self.db()) as conn, conn:
            if actor == 'morlet':
                rows = conn.execute(
                    'SELECT id,at,source,recipient,kind,text FROM events '
                    'WHERE id>? ORDER BY id LIMIT ?', (after, limit)).fetchall()
            else:
                rows = conn.execute(
                    'SELECT id,at,source,recipient,kind,text FROM events '
                    'WHERE id>? AND (recipient=? OR recipient=? OR source=?) '
                    'ORDER BY id LIMIT ?', (after, actor, 'all', actor, limit)).fetchall()
        return [dict(r) for r in rows]

    def poll(self, actor: str, after: int, timeout: float, limit: int) -> list[dict]:
        # Condición + doble consulta evita perder una notificación entre SELECT y wait.
        with self.changed:
            items = self.list_events(actor, after, limit)
            if items or timeout == 0:
                return items
            # La condición puede despertar por mensajes destinados a otro rol.
            self.changed.wait(timeout)
            return self.list_events(actor, after, limit)

    def make_task(self, agents: list[str], prompt: str) -> str:
        task_id = uuid4().hex
        with closing(self.db()) as conn, conn:
            conn.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?)',
                         (task_id, now(), 'queued', prompt, json.dumps(agents), '{}'))
        return task_id

    def update_task(self, task_id: str, state: str, result: dict) -> None:
        with closing(self.db()) as conn, conn:
            conn.execute('UPDATE tasks SET status=?,result=? WHERE id=?',
                         (state, json.dumps(result, ensure_ascii=False), task_id))
        with self.changed:
            self.changed.notify_all()

    def get_task(self, task_id: str) -> dict | None:
        with closing(self.db()) as conn, conn:
            row = conn.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
        if not row:
            return None
        return {**dict(row), 'agents': json.loads(row['agents']),
                'result': json.loads(row['result'])}


class Bridge(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr: tuple[str, int], store: Store, tokens: dict[str, str],
                 *, enable_api: bool = False, max_tasks: int = 3, responder=None):
        if addr[0] not in ('127.0.0.1', '::1', 'localhost'):
            raise ValueError('Solo se permite enlace local; use proxy HTTPS seguro si es necesario')
        self.store = store
        self.tokens = dict(tokens)
        self.enable_api = enable_api
        self.max_tasks = max_tasks
        self.task_count = 0
        self.dispatch_lock = threading.Lock()
        self.responder = responder or providers.answer
        super().__init__(addr, Handler)

    def dispatch(self, task_id: str, agents: list[str], prompt: str) -> None:
        def worker():
            results = {}
            self.store.update_task(task_id, 'running', results)
            for agent in agents:
                try:
                    text = self.responder(agent, prompt)
                    if not isinstance(text, str) or not text.strip():
                        raise providers.ProviderError('Sin respuesta de texto')
                    self.store.publish(agent, 'morlet', 'answer', text[:8000])
                    results[agent] = {'status': 'completed', 'text': text[:8000]}
                except Exception:
                    # No volcar tracebacks ni material secreto del proveedor.
                    results[agent] = {'status': 'error', 'message': 'Proveedor falló; revisar configuración'}
                self.store.update_task(task_id, 'running', results)
            state = 'completed' if all(x['status'] == 'completed' for x in results.values()) else 'partial'
            self.store.update_task(task_id, state, results)
        threading.Thread(target=worker, daemon=True, name='matick-task-' + task_id[:8]).start()


class Handler(BaseHTTPRequestHandler):
    server: Bridge
    server_version = 'MatickSyncBridge/' + __version__

    def log_message(self, fmt, *args):
        # No registrar tokens, mensajes ni contenidos de URL.
        return

    def _reply(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(int(code))
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _actor(self) -> str | None:
        supplied = self.headers.get('Authorization', '')
        if not supplied.startswith('Bearer '):
            self._reply(HTTPStatus.UNAUTHORIZED, {'error': 'Token requerido'})
            return None
        supplied = supplied[7:]
        for role, secret in self.server.tokens.items():
            if hmac.compare_digest(supplied, secret):
                return role
        self._reply(HTTPStatus.UNAUTHORIZED, {'error': 'Token inválido'})
        return None

    def _body(self) -> dict | None:
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            size = 0
        if not 0 < size <= MAX_BODY:
            self._reply(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {'error': 'Máximo 8 KiB'})
            return None
        try:
            obj = json.loads(self.rfile.read(size))
        except (json.JSONDecodeError, UnicodeError):
            self._reply(HTTPStatus.BAD_REQUEST, {'error': 'JSON no válido'})
            return None
        if not isinstance(obj, dict):
            self._reply(HTTPStatus.BAD_REQUEST, {'error': 'Se espera un objeto'})
            return None
        return obj

    def do_GET(self):
        path = urlsplit(self.path)
        if path.path == '/health':
            self._reply(200, {'service': 'matick-sync-bridge', 'status': 'ok',
                              'version': __version__})
            return
        role = self._actor()
        if not role:
            return
        if path.path == '/v1/status':
            self._reply(200, {'role': role, 'mode': 'local',
                              'api_dispatch_enabled': self.server.enable_api,
                              'configured_agents': [x for x in sorted(providers.ALLOWED)
                                                    if providers.configured(x)],
                              'remaining_tasks': max(0, self.server.max_tasks - self.server.task_count)})
            return
        if path.path == '/v1/poll':
            params = parse_qs(path.query)
            try:
                after = int(params.get('after', ['0'])[0])
                wait = float(params.get('wait', ['0'])[0])
                limit = int(params.get('limit', ['50'])[0])
                if after < 0 or not 0 <= wait <= MAX_POLL or not 1 <= limit <= 100:
                    raise ValueError()
            except (TypeError, ValueError, OverflowError):
                self._reply(400, {'error': 'after, wait o limit fuera de rango'})
                return
            events = self.server.store.poll(role, after, wait, limit)
            self._reply(200, {'events': events, 'next_after': events[-1]['id'] if events else after})
            return
        if path.path.startswith('/v1/tasks/'):
            if role != 'morlet':
                self._reply(403, {'error': 'Solo Morlet puede consultar tareas'})
                return
            task_id = path.path[len('/v1/tasks/'):]
            if len(task_id) != 32 or not all(c in '0123456789abcdef' for c in task_id):
                self._reply(400, {'error': 'Identificador inválido'})
                return
            data = self.server.store.get_task(task_id)
            self._reply(200, data) if data else self._reply(404, {'error': 'No existe'})
            return
        self._reply(404, {'error': 'Ruta no encontrada'})

    def do_POST(self):
        route = urlsplit(self.path)
        if route.path not in ('/v1/events', '/v1/tasks'):
            self._reply(404, {'error': 'Ruta no encontrada'})
            return
        role = self._actor()
        if not role:
            return
        data = self._body()
        if data is None:
            return
        if route.path == '/v1/events':
            recipient, kind, text = data.get('recipient'), data.get('kind'), data.get('text')
            client_id = data.get('client_id')
            if (recipient not in DESTINATIONS or not isinstance(kind, str) or
                not 1 <= len(kind) <= 32 or not kind.replace('-', '').replace('_', '').isalnum() or
                not isinstance(text, str) or not 1 <= len(text) <= MAX_TEXT or
                (client_id is not None and (not isinstance(client_id, str) or len(client_id) > 80))):
                self._reply(400, {'error': 'recipient, kind, text o client_id inválidos'})
                return
            if role != 'morlet' and recipient not in ('morlet', 'all'):
                # No permitir que un agente reenvíe órdenes a otro agente por sí solo.
                self._reply(403, {'error': 'Agentes solo responden a Morlet o al canal público'})
                return
            eid = self.server.store.publish(role, recipient, kind, text, client_id)
            self._reply(201, {'id': eid, 'source': role, 'recipient': recipient})
            return
        # Una tarea solo se factura si Morlet la solicita explícitamente y activó APIs.
        if role != 'morlet':
            self._reply(403, {'error': 'Solo Morlet puede ejecutar tareas con API'})
            return
        prompt, agents = data.get('prompt'), data.get('agents')
        if (not isinstance(prompt, str) or not 1 <= len(prompt) <= 4000 or
            not isinstance(agents, list) or not 1 <= len(agents) <= 3 or
            len(set(str(a) for a in agents)) != len(agents) or
            any(not isinstance(a, str) or a not in providers.ALLOWED for a in agents)):
            self._reply(400, {'error': 'prompt o agents inválidos'})
            return
        if not self.server.enable_api:
            self._reply(409, {'error': 'APIs desactivadas. Habilitar MATICK_SYNC_ENABLE_API=1 conscientemente'})
            return
        unconfigured = [a for a in agents if not providers.configured(a)]
        if unconfigured:
            self._reply(422, {'error': 'Agentes sin clave/modelo', 'agents': unconfigured})
            return
        with self.server.dispatch_lock:
            if self.server.task_count >= self.server.max_tasks:
                self._reply(429, {'error': 'Límite de tareas API alcanzado en este arranque'})
                return
            self.server.task_count += 1
        task_id = self.server.store.make_task(agents, prompt)
        self.server.store.publish('morlet', 'all', 'task', 'Tarea enviada a: ' + ', '.join(agents))
        self.server.dispatch(task_id, agents, prompt)
        self._reply(202, {'task_id': task_id, 'status': 'queued', 'agents': agents})


def main() -> None:
    tokens = load_tokens()
    port = int(os.getenv('MATICK_SYNC_PORT', '8788'))
    if not 1 <= port <= 65535:
        raise ValueError('Puerto inválido')
    enable = os.getenv('MATICK_SYNC_ENABLE_API') == '1'
    cap = min(25, max(1, int(os.getenv('MATICK_SYNC_MAX_TASKS', '3'))))
    srv = Bridge(('127.0.0.1', port), Store(os.getenv('MATICK_SYNC_DB') or default_db()),
                 tokens, enable_api=enable, max_tasks=cap)
    print(f'Matick Sync Bridge v{__version__} en http://127.0.0.1:{port} (local)')
    print('APIs externas: ' + ('HABILITADAS bajo petición explícita' if enable else 'DESACTIVADAS'))
    try:
        srv.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == '__main__':
    main()
