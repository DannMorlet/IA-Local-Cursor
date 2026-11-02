"""Pruebas sin GPU ni modelos: contrato de la sonda optativa de chat."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from smoke_inference import ProbeError, probe


class SmokeInferenceTests(unittest.TestCase):
    def setUp(self):
        self.servers = []

    def tearDown(self):
        for server, worker in self.servers:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)

    def serve(self, handler):
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.servers.append((server, worker))
        return "http://127.0.0.1:%d" % server.server_port

    def test_valid_http_chat_reports_only_observed_metrics(self):
        seen = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                seen.append((self.path, self.headers.get("Authorization"),
                             json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                data = json.dumps({"model": "qwen-test", "content": "Hola",
                    "stats": {"input_tokens": 12, "total_output_tokens": 3,
                              "tokens_per_second": "9999"}}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            def log_message(self, *args):
                pass

        result = probe(self.serve(Handler), "token-de-prueba", "qwen-test")
        self.assertEqual(result["estado"], "APROBADO_CONTRATO_HTTP")
        self.assertEqual(result["inferencia_con_pesos_reales"], "SIN_PROBAR")
        self.assertGreaterEqual(result["http_roundtrip_ms_medido"], 0)
        self.assertEqual(result["metricas_reportadas_por_proveedor"],
                         {"input_tokens": 12, "total_output_tokens": 3})
        self.assertEqual(seen[0][0], "/v1/chat")
        self.assertEqual(seen[0][1], "Bearer token-de-prueba")
        self.assertEqual(seen[0][2]["model"], "qwen-test")

    def test_empty_or_invalid_json_does_not_pass(self):
        for response in (b"not-json", b'{"content": ""}', b'{"content": 12}'):
            class Handler(BaseHTTPRequestHandler):
                def do_POST(self):
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(response)
                def log_message(self, *args):
                    pass
            with self.subTest(response=response):
                url = self.serve(Handler)
                with self.assertRaises(ProbeError):
                    probe(url, "secret")

    def test_model_mismatch_fails(self):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                data = b'{"model":"different","content":"Hola"}'
                self.send_response(200)
                self.end_headers()
                self.wfile.write(data)
            def log_message(self, *args):
                pass
        with self.assertRaisesRegex(ProbeError, "MODELO_NO_COINCIDE"):
            probe(self.serve(Handler), "secret", "expected")

    def test_redirect_never_forwards_bearer(self):
        received = []
        class Target(BaseHTTPRequestHandler):
            def do_GET(self):
                received.append(self.headers.get("Authorization"))
                self.send_response(200)
                self.end_headers()
            def do_POST(self):
                self.do_GET()
            def log_message(self, *args):
                pass
        target = self.serve(Target)

        class Source(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(302)
                self.send_header("Location", target + "/steal")
                self.end_headers()
            def log_message(self, *args):
                pass
        with self.assertRaisesRegex(ProbeError, "HTTP_302"):
            probe(self.serve(Source), "secret")
        self.assertEqual(received, [])

    def test_remote_http_and_missing_token_rejected(self):
        with self.assertRaisesRegex(ProbeError, "HTTP_SOLO_LOOPBACK"):
            probe("http://example.org", "secret")
        with self.assertRaisesRegex(ProbeError, "TOKEN_NO_CONFIGURADO"):
            probe("http://127.0.0.1:8787", "")
        with self.assertRaisesRegex(ProbeError, "URL_INVALIDA"):
            probe("http://127.0.0.1:bad", "secret")


if __name__ == "__main__":
    unittest.main()
