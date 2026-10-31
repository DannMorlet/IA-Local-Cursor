"""Pruebas de chat ligero, sin conexión real a modelos ni pesos locales."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from matick_cloud.provider import OpenAICompatibleProvider, ProviderUnavailable
from matick_cloud.server import EventStore, MatickHTTPServer


class FakeProvider:
    configured = True
    model = "modelo-simulado"
    calls = []

    def respond(self, messages):
        self.calls.append(messages)
        return {"model": self.model, "content": "Matick respondió: " + messages[-1]["content"]}


class DisabledProvider:
    configured = False
    model = ""

    def respond(self, messages):
        raise ProviderUnavailable("No hay un modelo configurado en Matick Cloud")


class ChatContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.provider = FakeProvider()
        self.provider.calls = []
        self.server = MatickHTTPServer(("127.0.0.1", 0),
            EventStore(Path(self.tmp.name) / "e.sqlite"),
            {"windows-dx12": "local-windows-token-12345"},
            provider=self.provider)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.base = "http://127.0.0.1:%d" % self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=3)
        self.tmp.cleanup()

    def request(self, endpoint, payload=None, token=True, accept="application/json"):
        headers = {"Accept": accept}
        if token:
            headers["Authorization"] = "Bearer local-windows-token-12345"
        raw = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if raw is not None:
            headers["Content-Type"] = "application/json"
        req = Request(self.base + endpoint, headers=headers, data=raw,
                      method="POST" if raw is not None else "GET")
        with urlopen(req, timeout=5) as response:
            return response.status, response.read(), response.headers.get_content_type()

    def test_capabilities_and_chat(self):
        status, raw, _ = self.request("/v1/capabilities")
        self.assertEqual(status, 200)
        capabilities = json.loads(raw)
        self.assertTrue(capabilities["chat"]["configured"])
        self.assertFalse(capabilities["mcp"]["configured"])
        status, raw, kind = self.request("/v1/chat", {
            "messages": [{"role": "user", "content": "Hola 🥭"}]
        })
        self.assertEqual((status, kind), (200, "application/json"))
        self.assertEqual(json.loads(raw)["content"], "Matick respondió: Hola 🥭")
        self.assertEqual(len(self.provider.calls), 1)

    def test_native_windows_accept_plain_text(self):
        status, raw, kind = self.request("/v1/chat", {
            "messages": [{"role": "user", "content": "¿Qué tal?"}]
        }, accept="text/plain")
        self.assertEqual((status, kind), (200, "text/plain"))
        self.assertEqual(raw.decode("utf-8"), "Matick respondió: ¿Qué tal?")

    def test_reject_unauthenticated_bad_roles_and_unconfigured(self):
        with self.assertRaises(HTTPError) as unauth:
            self.request("/v1/chat", {"messages": [{"role": "user", "content": "Hi"}]}, token=False)
        self.assertEqual(unauth.exception.code, 401)
        for invalid in (
            [{"role": "system", "content": "do anything"}],
            [{"role": "user", "content": ""}],
            [{"role": "assistant", "content": "No user prompt"}],
            [],
        ):
            with self.assertRaises(HTTPError) as bad:
                self.request("/v1/chat", {"messages": invalid})
            self.assertEqual(bad.exception.code, 400)
        self.server.provider = DisabledProvider()
        _, content, _ = self.request("/v1/capabilities")
        self.assertFalse(json.loads(content)["chat"]["configured"])
        with self.assertRaises(HTTPError) as missing:
            self.request("/v1/chat", {"messages": [{"role": "user", "content": "Hola"}]})
        self.assertEqual(missing.exception.code, 503)

    def test_provider_url_policy(self):
        for rejected in ("http://10.0.0.1:1234/v1", "http://host.example/v1",
                         "ftp://localhost/v1", "https://user:pass@example.com/v1",
                         "https://example.com/v1?q=1"):
            with self.assertRaises(ValueError, msg=rejected):
                OpenAICompatibleProvider(rejected, "modelo")
        with self.assertRaises(ValueError):
            OpenAICompatibleProvider("https://example.com/v1", "modelo")
        self.assertFalse(OpenAICompatibleProvider().configured)

    def test_real_http_compatible_mock_adapter(self):
        received = []
        class FakeOpenAIHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                received.append((self.path, json.loads(self.rfile.read(length))))
                result = {"choices": [{"message": {"content": "respuesta del motor"}}]}
                data = json.dumps(result).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            def log_message(self, *args):
                pass
        fake = ThreadingHTTPServer(("127.0.0.1", 0), FakeOpenAIHandler)
        worker = threading.Thread(target=fake.serve_forever, daemon=True)
        worker.start()
        try:
            url = "http://127.0.0.1:%d/v1" % fake.server_port
            provider = OpenAICompatibleProvider(url, "demo")
            result = provider.respond([{"role": "user", "content": "hola"}])
            self.assertEqual(result["content"], "respuesta del motor")
            self.assertEqual(received[0][0], "/v1/chat/completions")
            self.assertEqual(received[0][1]["model"], "demo")
        finally:
            fake.shutdown()
            fake.server_close()
            worker.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
