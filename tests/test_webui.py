import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from manguito.gateway import Manguito, make_handler


class WebUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.app = Manguito(cls.root, "1234567890" * 4, "http://127.0.0.1:1234/v1")
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cls.app))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.temp.cleanup()

    def test_home_is_styled(self):
        with urlopen(self.base + "/") as response:
            data = response.read().decode("utf-8")
            self.assertIn("Manguito Studio", data)
            self.assertIn("/assets/app.js", data)
            self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")

    def test_static_assets_are_served(self):
        for path, mime, snippet in [
            ("/assets/app.js", "text/javascript", "manguito_token"),
            ("/assets/style.css", "text/css", ".sidebar"),
        ]:
            with self.subTest(path=path), urlopen(self.base + path) as response:
                self.assertTrue(response.headers["Content-Type"].startswith(mime))
                self.assertIn(snippet, response.read().decode("utf-8"))

    def test_unknown_asset_does_not_escape_package(self):
        with self.assertRaises(HTTPError) as context:
            urlopen(self.base + "/assets/../../README.md")
        self.assertNotEqual(context.exception.code, 200)

    def test_private_status_requires_token(self):
        with self.assertRaises(HTTPError) as context:
            urlopen(self.base + "/v1/status")
        self.assertEqual(context.exception.code, 401)
        req = Request(self.base + "/v1/status",
                      headers={"Authorization": "Bearer " + self.app.token})
        with urlopen(req) as response:
            body = json.load(response)
        self.assertEqual(body["name"], "Manguito")
        self.assertFalse(body["writes"])


if __name__ == "__main__":
    unittest.main()
