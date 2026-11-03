"""Regresión REST: no presentar una respuesta de otro modelo como inferencia exitosa."""
from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from matick_cloud.provider import OpenAICompatibleProvider
from matick_cloud.server import EventStore, MatickHTTPServer


class IdentityIntegrationTests(unittest.TestCase):
    def test_wrong_model_returns_502_without_exposing_provider_text(self):
        class Engine(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                data = json.dumps({"model": "otro-modelo", "choices": [
                    {"message": {"content": "respuesta que no debe mostrarse"}}
                ]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        engine = ThreadingHTTPServer(("127.0.0.1", 0), Engine)
        engine_thread = threading.Thread(target=engine.serve_forever, daemon=True)
        engine_thread.start()
        with tempfile.TemporaryDirectory() as tmp:
            provider = OpenAICompatibleProvider(
                "http://127.0.0.1:%d/v1" % engine.server_port, "modelo-elegido"
            )
            app = MatickHTTPServer(
                ("127.0.0.1", 0), EventStore(Path(tmp) / "events.sqlite"),
                {"windows-dx12": "token-de-prueba-seguro"}, provider=provider
            )
            app_thread = threading.Thread(target=app.serve_forever, daemon=True)
            app_thread.start()
            try:
                req = Request(
                    "http://127.0.0.1:%d/v1/chat" % app.server_port,
                    data=json.dumps({"messages": [
                        {"role": "user", "content": "Hola"}
                    ]}).encode(),
                    headers={"Authorization": "Bearer token-de-prueba-seguro",
                             "Content-Type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(HTTPError) as failure:
                    urlopen(req, timeout=5)
                self.assertEqual(failure.exception.code, 502)
                error_body = failure.exception.read().decode()
                self.assertNotIn("respuesta que no debe mostrarse", error_body)
            finally:
                app.shutdown()
                app.server_close()
                app_thread.join(timeout=3)
        engine.shutdown()
        engine.server_close()
        engine_thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
