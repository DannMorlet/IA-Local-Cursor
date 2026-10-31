"""Pruebas REST v1 Matick: modelo, perfiles, permisos y chat sin modelos reales."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from matick_cloud.models import RestV1Bridge, ModelState, valid_params, PARAMS, LOAD_PARAMS
from matick_cloud.server import EventStore, MatickHTTPServer


class RestMock(BaseHTTPRequestHandler):
    requests = []
    def do_GET(self):
        if self.path == "/api/v1/models/download/status/job_1":
            self._reply({"job_id": "job_1", "status": "completed",
                         "total_size_bytes": 100, "downloaded_bytes": 100})
            return
        if self.path != "/api/v1/models":
            self.send_error(404)
            return
        self._reply({"models": [
            {"key": "google/gemma-demo", "display_name": "Gemma Demo",
             "type": "llm", "loaded_instances": [], "size_bytes": 1000},
            {"key": "qwen/qwen-demo", "display_name": "Qwen Demo",
             "type": "llm", "loaded_instances": [{"id": "instance-1"}],
             "size_bytes": 2000}
        ]})

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        self.__class__.requests.append((self.path, data))
        if self.path == "/api/v1/models/load":
            self._reply({"status": "loaded", "instance_id": data["model"],
                         "load_config": data})
        elif self.path == "/api/v1/models/unload":
            self._reply({"instance_id": data["instance_id"]})
        elif self.path == "/api/v1/chat":
            self._reply({"output": [{"type": "message", "content": "Respuesta v1: " + data["input"]}],
                         "stats": {"tokens_per_second": 42},
                         "response_id": "resp_demo_2026" if data.get("store") else None,
                         "model_instance_id": "demo-instance"})
        elif self.path == "/api/v1/models/download":
            self._reply({"job_id": "job_1", "status": "downloading"})
        else:
            self.send_error(404)

    def _reply(self, value):
        data = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def log_message(self, *args):
        pass


class RestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        RestMock.requests = []
        self.upstream = ThreadingHTTPServer(("127.0.0.1", 0), RestMock)
        self.up_thread = threading.Thread(target=self.upstream.serve_forever, daemon=True)
        self.up_thread.start()
        self.bridge = RestV1Bridge("http://127.0.0.1:%d" % self.upstream.server_port)
        self.server = MatickHTTPServer(("127.0.0.1", 0),
            EventStore(Path(self.temp.name) / "db.sqlite"),
            {"windows-dx12": "windows-private-token-1234", "matick-chat": "chat-private-token-123456"},
            rest=self.bridge)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:%d" % self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.upstream.shutdown()
        self.upstream.server_close()
        self.up_thread.join(timeout=3)
        self.temp.cleanup()

    def call(self, path, data=None, role="windows-dx12"):
        headers = {"Authorization": "Bearer " + (
            "windows-private-token-1234" if role == "windows-dx12" else "chat-private-token-123456")}
        raw = json.dumps(data).encode() if data is not None else None
        req = Request(self.url + path, method="POST" if raw is not None else "GET",
                      data=raw, headers=headers)
        with urlopen(req, timeout=5) as resp:
            return json.load(resp)

    def test_models_load_select_chat_unload(self):
        catalog = self.call("/v1/models")
        self.assertEqual(len(catalog["models"]), 2)
        active = self.call("/v1/models/settings", {"model": "google/gemma-demo",
            "generation": {"temperature": 0.4, "top_k": 40, "max_output_tokens": 256},
            "load": {"context_length": 4096, "flash_attention": True}})
        self.assertEqual(active["model"], "google/gemma-demo")
        self.assertEqual(self.call("/v1/models/settings")["generation"]["top_k"], 40)
        loaded = self.call("/v1/models/load", {
            "model": "google/gemma-demo", "params": {"context_length": 4096, "flash_attention": True}})
        self.assertEqual(loaded["loaded"]["status"], "loaded")
        self.assertEqual(RestMock.requests[-1][1]["context_length"], 4096)
        chat = self.call("/v1/chat", {"messages": [{"role": "user", "content": "hola"}]})
        self.assertIn("Respuesta v1:", chat["content"])
        self.assertEqual(RestMock.requests[-1][1]["temperature"], 0.4)
        unloaded = self.call("/v1/models/unload", {"instance_id": "google/gemma-demo",
                                                    "model": "google/gemma-demo"})
        self.assertIsNone(self.call("/v1/models/settings")["model"])
        self.assertIn("unloaded", unloaded)

    def test_rest_v1_0428_stateful_and_metadata(self):
        models = self.call("/v1/models")["models"]
        self.assertEqual(models[0]["key"], "google/gemma-demo")
        self.assertEqual(models[1]["loaded_instances"][0]["id"], "instance-1")
        self.call("/v1/models/settings", {"model": "google/gemma-demo"})
        first = self.call("/v1/chat", {
            "stateful": True,
            "messages": [{"role": "user", "content": "primer turno"}]
        })
        self.assertEqual(first["response_id"], "resp_demo_2026")
        self.assertEqual(first["model_instance_id"], "demo-instance")
        previous = self.call("/v1/chat", {
            "stateful": True, "previous_response_id": first["response_id"],
            "messages": [{"role": "user", "content": "primer turno"},
                         {"role": "assistant", "content": "respuesta"},
                         {"role": "user", "content": "segundo turno"}]
        })
        self.assertEqual(previous["response_id"], "resp_demo_2026")
        upstream = RestMock.requests[-1][1]
        self.assertEqual(upstream["input"], "segundo turno")
        self.assertEqual(upstream["previous_response_id"], first["response_id"])
        self.assertTrue(upstream["store"])
        with self.assertRaises(HTTPError) as invalid:
            self.call("/v1/chat", {
                "previous_response_id": "../bad",
                "stateful": True,
                "messages": [{"role": "user", "content": "hola"}]
            })
        self.assertEqual(invalid.exception.code, 502)

    def test_permissions_and_invalid_parameters(self):
        with self.assertRaises(HTTPError) as denied:
            self.call("/v1/models/settings", {"model": "google/gemma-demo"}, role="matick-chat")
        self.assertEqual(denied.exception.code, 403)
        with self.assertRaises(HTTPError) as bad:
            self.call("/v1/models/settings", {"generation": {"temperature": 5}})
        self.assertEqual(bad.exception.code, 400)
        with self.assertRaises(HTTPError):
            self.call("/v1/models/load", {"model": "fake/model"})
        with self.assertRaises(HTTPError) as blocked:
            self.call("/v1/models/download", {"model": "google/gemma-demo"})
        self.assertEqual(blocked.exception.code, 403)
        self.assertEqual(len(RestMock.requests), 0)
        with self.assertRaises(HTTPError):
            self.call("/v1/models/download/status?job_id=not_a_job")

    def test_upstream_security_and_state_persistence(self):
        with self.assertRaises(ValueError):
            RestV1Bridge("http://192.168.76.1:1234")
        with self.assertRaises(ValueError):
            RestV1Bridge("https://model.remote.example")
        with self.assertRaises(ValueError):
            valid_params({"flash_attention": 1}, LOAD_PARAMS)
        with self.assertRaises(ValueError):
            valid_params({"temperature": float("nan")}, PARAMS)
        self.call("/v1/models/settings", {"model": "qwen/qwen-demo",
             "generation": {"max_output_tokens": 128}})
        reloaded = ModelState(Path(self.temp.name) / "db.sqlite")
        self.assertEqual(reloaded.get()["model"], "qwen/qwen-demo")


if __name__ == "__main__":
    unittest.main()
