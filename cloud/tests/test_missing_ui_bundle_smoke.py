"""Regression: missing UI bundles must fail visibly instead of returning blank HTML.

Run: PYTHONPATH=cloud python -m unittest discover -s cloud/tests -p 'test_*.py'
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from matick_cloud.server import EventStore, MatickHTTPServer


class MissingAssetSmokeTests(TestCase):
    def test_missing_bundle_is_404_while_health_remains_available(self) -> None:
        with TemporaryDirectory(prefix="matick missing asset ") as folder:
            server = MatickHTTPServer(
                ("127.0.0.1", 0),
                EventStore(Path(folder) / "events.sqlite"),
                {"matick-chat": "test-token-at-least-sixteen-chars"},
            )
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                # Simulate a damaged installation with the JavaScript bundle absent.
                # A 200 HTML fallback would leave the window visually blank.
                with patch.object(Path, "read_bytes", side_effect=FileNotFoundError):
                    with self.assertRaises(HTTPError) as missing:
                        urlopen(base + "/app/app.js", timeout=3)
                    self.assertEqual(missing.exception.code, 404)
                    payload = json.loads(missing.exception.read())
                    self.assertIn("error", payload)
                    self.assertEqual(missing.exception.headers.get("X-Content-Type-Options"), "nosniff")

                # A zero-byte bundle is equally damaging: reject it rather
                # than serving HTTP 200 with a blank script.
                with patch.object(Path, "read_bytes", return_value=b""):
                    with self.assertRaises(HTTPError) as empty:
                        urlopen(base + "/app/app.js", timeout=3)
                    self.assertEqual(empty.exception.code, 503)
                    self.assertIn("vacío", json.loads(empty.exception.read())["error"])
                    self.assertEqual(empty.exception.headers.get("X-Content-Type-Options"), "nosniff")

                # Recovery must work in the same running server once the
                # simulated missing asset is restored. Otherwise a cached
                # failure can keep the installed window blank until restart.
                with urlopen(base + "/app/app.js", timeout=3) as recovered:
                    self.assertEqual(recovered.status, 200)
                    self.assertIn("javascript", recovered.headers["Content-Type"])
                    self.assertTrue(recovered.read().strip(), "restored app.js is empty")
                    self.assertEqual(
                        recovered.headers.get("X-Content-Type-Options"), "nosniff"
                    )

                # A healthy backend is not evidence that all UI assets exist.
                with urlopen(base + "/health", timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(json.load(response)["status"], "ok")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    import unittest
    unittest.main()
