"""Regresión: el cliente CLI nunca reenvía tokens Bearer al seguir redirecciones."""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from matick_cloud.client import request


class TokenCollector(BaseHTTPRequestHandler):
    seen = []

    def do_GET(self):
        self.__class__.seen.append(self.headers.get("Authorization"))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "unexpected"}')

    def log_message(self, *args):
        pass


class RedirectingServer(BaseHTTPRequestHandler):
    target_port = 0

    def do_GET(self):
        if self.path == "/ok":
            raw = json.dumps({"status": "ok"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        self.send_response(302)
        self.send_header("Location", "http://127.0.0.1:%d/collect" % self.target_port)
        self.end_headers()

    def log_message(self, *args):
        pass


class ClientRedirectTests(unittest.TestCase):
    def setUp(self):
        TokenCollector.seen = []
        self.collector = ThreadingHTTPServer(("127.0.0.1", 0), TokenCollector)
        RedirectingServer.target_port = self.collector.server_port
        self.source = ThreadingHTTPServer(("127.0.0.1", 0), RedirectingServer)
        self.threads = []
        for server in (self.collector, self.source):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.threads.append(thread)

    def tearDown(self):
        for server in (self.source, self.collector):
            server.shutdown()
            server.server_close()
        for thread in self.threads:
            thread.join(timeout=3)

    def test_redirect_does_not_leak_bearer_token_and_normal_calls_work(self):
        env = {
            "MATICK_CLOUD_URL": "http://127.0.0.1:%d" % self.source.server_port,
            "MATICK_TOKEN": "role-secret-for-local-test",
        }
        with patch.dict(os.environ, env):
            with self.assertRaises(HTTPError) as blocked:
                request("GET", "/v1/status")
            self.assertEqual(blocked.exception.code, 302)
            blocked.exception.close()
            self.assertEqual(TokenCollector.seen, [])
            self.assertEqual(request("GET", "/ok"), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
