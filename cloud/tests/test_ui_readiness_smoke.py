"""HTTP integration tests for the UI readiness preflight endpoint."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from matick_cloud.server import EventStore, MatickHTTPServer


class UIReadinessTests(TestCase):
    def test_preflight_detects_blank_assets_and_recovers(self):
        with TemporaryDirectory(prefix="matick readiness ") as folder:
            server = MatickHTTPServer(
                ("127.0.0.1", 0),
                EventStore(Path(folder) / "events.sqlite"),
                {"matick-chat": "test-token-at-least-sixteen-chars"},
            )
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(base + "/health/ui", timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    data = json.load(response)
                    self.assertEqual(data["status"], "ok")
                    self.assertEqual(data["assets_checked"], 7)
                    self.assertNotIn("token", str(data).lower())

                with patch.object(Path, "read_bytes", return_value=b" \t\n"):
                    with self.assertRaises(HTTPError) as error:
                        urlopen(base + "/health/ui", timeout=3)
                    self.assertEqual(error.exception.code, 503)
                    data = json.load(error.exception)
                    self.assertEqual(data["status"], "degraded")
                    self.assertEqual(len(data["assets"]), 7)
                    self.assertNotIn(str(folder), str(data))

                with patch.object(Path, "read_bytes", side_effect=FileNotFoundError):
                    with self.assertRaises(HTTPError) as error:
                        urlopen(base + "/health/ui", timeout=3)
                    self.assertEqual(error.exception.code, 503)

                with urlopen(base + "/health/ui", timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(json.load(response)["status"], "ok")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)
