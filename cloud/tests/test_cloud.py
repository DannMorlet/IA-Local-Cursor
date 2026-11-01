"""Pruebas sin dependencia de servicios externos."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from matick_cloud.server import EventStore, MatickHTTPServer, load_tokens


class CloudTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "events.db"
        self.tokens = {
            "matick-studio-lm": "studio-token-0123456789",
            "matick-chat": "chat-token-01234567890",
        }
        self.server = MatickHTTPServer(("127.0.0.1", 0), EventStore(self.db), self.tokens)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:%d" % self.server.server_port
        self.addCleanup(self._stop)

    def _stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def call(self, path: str, role: str | None = None, body: dict | None = None) -> tuple[int, dict]:
        headers = {}
        if role:
            headers["Authorization"] = "Bearer " + self.tokens[role]
        data = json.dumps(body).encode("utf-8") if body is not None else None
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = Request(self.base + path, data=data, headers=headers,
                      method="POST" if data is not None else "GET")
        with urlopen(req, timeout=3) as resp:
            return resp.status, json.load(resp)

    def test_public_health_and_authenticated_status(self) -> None:
        status, health = self.call("/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")
        _, info = self.call("/v1/status", "matick-chat")
        self.assertEqual(info["actor"], "matick-chat")
        with self.assertRaises(HTTPError) as denied:
            self.call("/v1/status")
        self.assertEqual(denied.exception.code, 401)

    def test_non_ascii_bearer_token_returns_401_and_server_recovers(self) -> None:
        # http.client accepts Latin-1 in headers; compare_digest(str, str)
        # used to raise TypeError and abruptly close the connection.
        req = Request(self.base + "/v1/status", headers={
            "Authorization": "Bearer inválido",
        })
        with self.assertRaises(HTTPError) as denied:
            urlopen(req, timeout=3)
        self.assertEqual(denied.exception.code, 401)
        self.assertEqual(json.load(denied.exception)["error"], "Token inválido")
        # A malformed credential must not break the next valid request.
        status, data = self.call("/v1/status", "matick-chat")
        self.assertEqual(status, 200)
        self.assertEqual(data["actor"], "matick-chat")

    def test_unicode_configured_token_is_supported(self) -> None:
        # Secrets from MATICK_TOKENS_JSON are UTF-8 strings; keep support
        # for valid non-ASCII tokens while comparing constant-time bytes.
        self.server.tokens["matick-chat"] = "clave-segura-ñ-123456789"
        self.tokens["matick-chat"] = "clave-segura-ñ-123456789"
        status, data = self.call("/v1/status", "matick-chat")
        self.assertEqual(status, 200)
        self.assertEqual(data["actor"], "matick-chat")

    def test_message_is_bidirectional_and_isolated_by_recipient(self) -> None:
        status, receipt = self.call("/v1/events", "matick-studio-lm", {
            "target": "matick-chat", "kind": "mensaje", "payload": {"texto": "hola"},
            "source": "alexa",
        })
        self.assertEqual(status, 201)
        self.assertEqual(receipt["source"], "matick-studio-lm")
        _, inbox_chat = self.call("/v1/events?after=0", "matick-chat")
        self.assertEqual(len(inbox_chat["events"]), 1)
        self.assertEqual(inbox_chat["events"][0]["payload"], {"texto": "hola"})
        _, inbox_studio = self.call("/v1/events?after=0", "matick-studio-lm")
        self.assertEqual(inbox_studio["events"], [])

        self.call("/v1/events", "matick-chat", {
            "target": "matick-studio-lm", "kind": "respuesta", "payload": {"ok": True},
        })
        _, replied = self.call("/v1/events?after=0", "matick-studio-lm")
        self.assertEqual(replied["events"][0]["source"], "matick-chat")
        _, cursor = self.call("/v1/events?after=%d" % replied["events"][0]["id"], "matick-studio-lm")
        self.assertEqual(cursor["events"], [])

    def test_validations_and_persistence(self) -> None:
        with self.assertRaises(HTTPError) as denied:
            self.call("/v1/events", "matick-chat", {
                "target": "desconocido", "kind": "x", "payload": {},
            })
        self.assertEqual(denied.exception.code, 400)
        with self.assertRaises(HTTPError) as invalid_type:
            self.call("/v1/events", "matick-chat", {
                "target": ["matick-studio-lm"], "kind": "x", "payload": {},
            })
        self.assertEqual(invalid_type.exception.code, 400)
        self.call("/v1/events", "matick-chat", {
            "target": "matick-studio-lm", "kind": "persist", "payload": {"n": 3},
        })
        reopened = EventStore(self.db)
        self.assertEqual(reopened.inbox("matick-studio-lm", 0, 10)[0]["payload"]["n"], 3)

    def test_token_validation(self) -> None:
        with self.assertRaises(ValueError):
            load_tokens('{"matick-chat":"abc"}')
        with self.assertRaises(ValueError):
            load_tokens('{"matick-chat":"same-long-token-123","alexa":"same-long-token-123"}')
        self.assertEqual(load_tokens(json.dumps(self.tokens)), self.tokens)


if __name__ == "__main__":
    unittest.main()
