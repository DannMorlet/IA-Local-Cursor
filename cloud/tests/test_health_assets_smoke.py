"""Regression: public health and web assets must not leak authentication secrets.

Run with PYTHONPATH=cloud python -m unittest discover -s cloud/tests -p 'test_*.py'
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from matick_cloud.server import EventStore, MatickHTTPServer


class HealthAndAssetsSmokeTests(unittest.TestCase):
    def test_public_health_assets_and_authentication_are_separate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="matick health smoke ") as folder:
            token = "secret-canary-not-for-public-responses-123456789"
            server = MatickHTTPServer(
                ("127.0.0.1", 0),
                EventStore(Path(folder) / "events.sqlite"),
                {"matick-chat": token},
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                # The health endpoint must work before any token is configured
                # in the client, without exposing credentials in its payload.
                with urlopen(base + "/health", timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    raw_health = response.read().decode("utf-8")
                    self.assertEqual(json.loads(raw_health)["status"], "ok")
                    self.assertNotIn(token, raw_health)

                # The UI's actual JavaScript asset must be served, not just
                # a successful HTML page masking a missing bundle.
                with urlopen(base + "/app/app.js", timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    script = response.read()
                    self.assertTrue(script.strip(), "app.js was empty")
                    self.assertNotIn(token.encode(), script)

                # Health alone cannot prove that the UI assets are installed.
                # Check each declared route, MIME type, content and token secrecy.
                assets = {
                    "/app": "text/html",
                    "/app/style.css": "text/css",
                    "/app/clare.css": "text/css",
                    "/app/chat_payload.mjs": "text/javascript",
                    "/app/clare.js": "text/javascript",
                    "/app/clare_behavior.mjs": "text/javascript",
                }
                for route, mime in assets.items():
                    with self.subTest(route=route):
                        with urlopen(base + route, timeout=3) as response:
                            self.assertEqual(response.status, 200)
                            self.assertIn(mime, response.headers["Content-Type"])
                            payload = response.read()
                            self.assertTrue(payload.strip(), route + " was empty")
                            self.assertNotIn(token.encode(), payload)
                            self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")

                # A healthy server must still refuse unauthenticated API
                # requests; a public /health is not proof of chat access.
                with self.assertRaises(HTTPError) as denied:
                    urlopen(base + "/v1/status", timeout=3)
                self.assertEqual(denied.exception.code, 401)

                request = Request(
                    base + "/v1/status",
                    headers={"Authorization": "Bearer " + token},
                )
                with urlopen(request, timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(json.load(response)["actor"], "matick-chat")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
