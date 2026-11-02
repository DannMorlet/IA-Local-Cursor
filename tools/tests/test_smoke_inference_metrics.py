"""Regresión: la sonda no debe presentar contadores de tokens imprecisos.

Pruebas HTTP simuladas; no certifican inferencia ni uso de GPU.
"""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from smoke_inference import probe


class SmokeMetricsTests(unittest.TestCase):
    def probe_with_stats(self, stats):
        payload = json.dumps({"model": "test-model", "content": "Hola", "stats": stats}).encode("utf-8")

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            return probe(f"http://127.0.0.1:{server.server_port}", "token-de-prueba", "test-model")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_fractional_and_unsafe_integer_token_counts_are_discarded(self):
        stats = {"input_tokens": 1.5, "total_output_tokens": (1 << 53),
                 "tokens_per_second": 21.5}
        observed = self.probe_with_stats(stats)["metricas_reportadas_por_proveedor"]
        self.assertEqual(observed, {"tokens_per_second": 21.5})

    def test_safe_integer_boundary_and_zero_are_preserved(self):
        stats = {"input_tokens": (1 << 53) - 1, "total_output_tokens": 0,
                 "tokens_per_second": 0.0}
        observed = self.probe_with_stats(stats)["metricas_reportadas_por_proveedor"]
        self.assertEqual(observed, stats)

    def test_boolean_negative_and_nonfinite_metrics_are_discarded(self):
        stats = {"input_tokens": True, "total_output_tokens": -3,
                 "tokens_per_second": float("nan")}
        observed = self.probe_with_stats(stats)["metricas_reportadas_por_proveedor"]
        self.assertEqual(observed, {})


if __name__ == "__main__":
    unittest.main()
