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
        from matick_cloud.server import ROLES
        self.tokens = {role: role + "-token-0123456789" for role in ROLES}
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

    def test_route_policy_and_status_surface(self) -> None:
        _, routes = self.call("/v1/routes", "matick-reloj")
        self.assertEqual(routes["allowed_targets"], ["chatgpt", "matick-studio-lm"])
        self.assertFalse(routes["can_fanout"])

        with self.assertRaises(HTTPError) as denied_peer:
            self.call("/v1/events", "matick-reloj", {
                "target": "matick-codex", "kind": "mensaje", "payload": {},
            })
        self.assertEqual(denied_peer.exception.code, 403)

        status, receipt = self.call("/v1/events", "matick-studio-lm", {
            "target": "matick-pet", "kind": "status.snapshot",
            "payload": {
                "component": "matick-studio-lm", "state": "working",
                "updated_at": "2026-10-30T17:00:00Z", "progress_pct": 20,
            },
        })
        self.assertEqual(status, 201)
        self.assertEqual(receipt["target"], "matick-pet")
        _, pet_inbox = self.call("/v1/events?after=0", "matick-pet")
        self.assertEqual(pet_inbox["events"][0]["kind"], "status.snapshot")

        with self.assertRaises(HTTPError) as denied_pet_message:
            self.call("/v1/events", "matick-chat", {
                "target": "matick-pet", "kind": "mensaje", "payload": {},
            })
        self.assertEqual(denied_pet_message.exception.code, 403)
        with self.assertRaises(HTTPError) as denied_pet_write:
            self.call("/v1/events", "matick-pet", {
                "target": "matick-studio-lm", "kind": "status.snapshot", "payload": {},
            })
        self.assertEqual(denied_pet_write.exception.code, 403)

        with self.assertRaises(HTTPError) as wrong_status_source:
            self.call("/v1/events", "chatgpt", {
                "target": "matick-pet", "kind": "status.snapshot", "payload": {},
            })
        self.assertEqual(wrong_status_source.exception.code, 403)
        with self.assertRaises(HTTPError) as private_status_data:
            self.call("/v1/events", "matick-studio-lm", {
                "target": "matick-pet", "kind": "status.snapshot",
                "payload": {
                    "component": "matick-studio-lm", "state": "working",
                    "updated_at": "2026-10-30T17:00:00Z", "pulso": 80,
                },
            })
        self.assertEqual(private_status_data.exception.code, 400)

    def test_director_fanout_is_explicit_and_authenticated(self) -> None:
        status, receipt = self.call("/v1/direct", "matick-studio-lm", {
            "targets": ["chatgpt", "matick-chat", "matick-codex"],
            "kind": "tarea.asignada", "payload": {"id": "t-7"},
        })
        self.assertEqual(status, 201)
        self.assertEqual([item["target"] for item in receipt["deliveries"]],
                         ["chatgpt", "matick-chat", "matick-codex"])
        for role in ("chatgpt", "matick-chat", "matick-codex"):
            _, inbox = self.call("/v1/events?after=0", role)
            self.assertEqual(inbox["events"][0]["payload"]["id"], "t-7")

        with self.assertRaises(HTTPError) as denied:
            self.call("/v1/direct", "matick-chat", {
                "targets": ["alexa", "matick-reloj"], "kind": "aviso", "payload": {},
            })
        self.assertEqual(denied.exception.code, 403)

        with self.assertRaises(HTTPError) as no_wildcard:
            self.call("/v1/direct", "matick-studio-lm", {
                "targets": ["chatgpt", "chatgpt"], "kind": "aviso", "payload": {},
            })
        self.assertEqual(no_wildcard.exception.code, 400)

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

