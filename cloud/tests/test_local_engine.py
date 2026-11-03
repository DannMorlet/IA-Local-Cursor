"""Pruebas del motor independiente. Fake llama-server HTTP, SIN pesos reales ni GPU."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from matick_cloud.local_engine import LocalLlamaEngine
from matick_cloud.models import ModelOffline, RestV1Bridge
from matick_cloud.provider import OpenAICompatibleProvider
from matick_cloud.server import EventStore, MatickHTTPServer


FAKE_SERVER = r'''#!/usr/bin/env python3
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
parser = argparse.ArgumentParser()
for key in ["host", "port", "model", "alias", "api-key", "ctx-size", "batch-size", "gpu-layers", "fit"]:
    parser.add_argument("--" + key)
parser.add_argument("--no-webui", action="store_true")
parser.add_argument("--flash-attn")
parser.add_argument("--no-kv-offload", action="store_true")
args = parser.parse_args()
class H(BaseHTTPRequestHandler):
    def send_json(self, obj, status=200):
        raw = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def do_GET(self):
        if self.path == "/health":
            self.send_json({"status": "ok"})
        elif self.headers.get("Authorization") != "Bearer " + args.api_key:
            self.send_json({"error": "unauthorized"}, 401)
        elif self.path == "/v1/models":
            self.send_json({"data": [{"id": args.alias, "object": "model"}]})
        else:
            self.send_json({"error": "not found"}, 404)
    def do_POST(self):
        if self.headers.get("Authorization") != "Bearer " + args.api_key:
            self.send_json({"error": "unauthorized"}, 401)
            return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        if self.path != "/v1/chat/completions" or body.get("model") != args.alias:
            self.send_json({"error": "invalid model"}, 400)
            return
        self.send_json({
            "model": args.alias,
            "choices": [{"message": {"content": "Respuesta GGUF simulada: " + body["messages"][-1]["content"]}}],
            "usage": {"prompt_tokens": 14, "completion_tokens": 7}
        })
    def log_message(self, *args):
        pass
ThreadingHTTPServer((args.host, int(args.port)), H).serve_forever()
'''


@unittest.skipIf(os.name == "nt", "El binario de prueba tiene shebang; se verifica en Linux CI")
class LocalEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "Matick Studio LM"
        (self.home / "engine").mkdir(parents=True)
        (self.home / "models").mkdir()
        self.exe = self.home / "engine" / "fake-llama-server"
        self.exe.write_text(FAKE_SERVER, encoding="utf-8")
        self.exe.chmod(0o755)
        self.file = self.home / "models" / "Mi modelo mexicano.gguf"
        self.file.write_bytes(b"GGUF test: no es un modelo real")
        self.engine = LocalLlamaEngine(self.home, executable=self.exe, startup_timeout=6)

    def tearDown(self):
        self.engine.close()
        self.tmp.cleanup()

    def test_catalog_load_chat_unload_real_http_fake_weights(self):
        models = self.engine.models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["format"], "GGUF")
        self.assertEqual(models[0]["name"], "Mi modelo mexicano")
        self.assertEqual(models[0]["loaded_instances"], [])
        key = models[0]["key"]
        loaded = self.engine.load(key, {"context_length": 4096, "eval_batch_size": 256,
                                        "flash_attention": True})
        self.assertEqual(loaded["status"], "loaded")
        self.assertEqual(self.engine.models()[0]["loaded_instances"][0]["id"], key)
        answer = self.engine.chat(key, [{"role": "user", "content": "Hola Morlet"}],
                                  {"temperature": 0.5, "top_k": 30, "max_output_tokens": 64})
        self.assertIn("Respuesta GGUF simulada", answer["content"])
        self.assertEqual(answer["model"], key)
        self.assertEqual(answer["stats"]["total_output_tokens"], 7)
        self.assertIn("top_k", answer["parameters_forwarded"])
        self.assertEqual(self.engine.unload(key)["status"], "unloaded")
        self.assertFalse(self.engine.models()[0]["loaded_instances"])
        with self.assertRaises(ModelOffline):
            self.engine.chat(key, [{"role": "user", "content": "hola"}], {})

    def test_invalid_model_path_and_missing_binary_are_safe(self):
        with self.assertRaisesRegex(ValueError, "GGUF disponible"):
            self.engine.load("../archivos-ajenos", {})
        with self.assertRaisesRegex(ValueError, "num_experts"):
            self.engine.load(self.engine.models()[0]["key"], {"num_experts": 16})
        self.exe.unlink()
        with self.assertRaises(ModelOffline):
            self.engine.load(self.engine.models()[0]["key"], {})

    def test_model_bytes_stay_in_place_after_unload(self):
        digest = self.file.read_bytes()
        key = self.engine.models()[0]["key"]
        self.engine.load(key, {})
        self.engine.unload(key)
        self.assertEqual(self.file.read_bytes(), digest)
        self.assertTrue(self.file.is_file())

    def test_matick_api_end_to_end_with_fake_llama_server(self):
        db = self.home / "matick-test.db"
        server = MatickHTTPServer(
            ("127.0.0.1", 0), EventStore(db),
            {"windows-dx12": "test-local-token-123456"},
            rest=RestV1Bridge(), provider=OpenAICompatibleProvider(),
            local_engine=self.engine
        )
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = "http://127.0.0.1:%d" % server.server_port
        def call(path, payload=None, token="test-local-token-123456"):
            raw = json.dumps(payload).encode() if payload is not None else None
            req = Request(base + path, data=raw,
                          headers={"Authorization": "Bearer " + token},
                          method="POST" if raw is not None else "GET")
            with urlopen(req, timeout=20) as response:
                return json.load(response)
        try:
            inventory = call("/v1/models")
            self.assertEqual(inventory["provider"], "llama.cpp-local")
            self.assertTrue(inventory["connected"])
            key = inventory["models"][0]["key"]
            with self.assertRaises(HTTPError) as denied:
                call("/v1/models/load", {"model": key}, token="bad-token")
            self.assertEqual(denied.exception.code, 401)
            accepted = call("/v1/models/load", {"model": key, "params": {"context_length": 4096}})
            self.assertEqual(accepted["loaded"]["engine"], "llama.cpp-local")
            generated = call("/v1/chat", {"messages": [{"role": "user", "content": "Hola Matick"}]})
            self.assertEqual(generated["model"], key)
            self.assertEqual(generated["engine"], "llama.cpp-local")
            self.assertIn("Hola Matick", generated["content"])
            with self.assertRaises(HTTPError) as bad_model:
                call("/v1/chat", {"model": "local/otro-modelo",
                                  "messages": [{"role": "user", "content": "Hola"}]})
            self.assertEqual(bad_model.exception.code, 503)
            call("/v1/models/unload", {"instance_id": key, "model": key})
            self.assertFalse(call("/v1/models")["models"][0]["loaded_instances"])
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=4)


if __name__ == "__main__":
    unittest.main()
