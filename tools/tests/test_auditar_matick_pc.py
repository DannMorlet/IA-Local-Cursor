"""Matick PC audit tests: 100% offline, never execute the fixture project."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import struct
import threading
import tempfile
import unittest
from pathlib import Path

from auditar_matick_pc import (
    scan, pe_x64, local_url, score_checks, markdown, api_json,
)

class MatickPcAuditTests(unittest.TestCase):
    def test_inventory_all_files_without_loading_private_or_giant_models(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "main.py").write_text("print('valid')\n", encoding="utf8")
            (root / "bad.py").write_text("def broken(:\n", encoding="utf8")
            (root / "package.json").write_text('{"name":"matick"}', encoding="utf8")
            (root / "broken.json").write_text("{broken", encoding="utf8")
            (root / ".env").write_text("PRIVATE_KEY=do_not_report", encoding="utf8")
            (root / "mcp.json").write_text('{"mcpServers":{"mascota":{"command":"python"}}}',
                                            encoding="utf8")
            (root / "cuda").mkdir()
            (root / "cuda" / "large.pt").write_bytes(b"model_bytes" * 50)
            files, issues, m = scan(root, deep=False, max_mb=1)
            self.assertEqual(m["files"], 7)
            self.assertEqual(m["py_bad"], 1)
            self.assertEqual(m["json_bad"], 1)
            self.assertEqual(m["mcp"], 1)
            self.assertEqual(m["mcp_bad"], 0)
            self.assertEqual(m["private"], 2)
            self.assertEqual(m["thirdparty"], 1)
            self.assertTrue(any(x["status"] if "status" in x else
                x["result"] == "privado: contenido no leído" for x in files))
            exposed = json.dumps(files, ensure_ascii=False)
            self.assertNotIn("do_not_report", exposed)
            self.assertNotIn("model_bytes", exposed)
            self.assertTrue(any(label == "Python inválido" for label, _ in issues))

    def test_detect_exe_without_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "MatickStudioLM.exe"
            data = bytearray(150)
            data[:2] = b"MZ"
            struct.pack_into("<I", data, 0x3c, 100)
            data[100:104] = b"PE\x00\x00"
            struct.pack_into("<H", data, 104, 0x8664)
            path.write_bytes(data)
            self.assertTrue(pe_x64(path))
            struct.pack_into("<H", data, 104, 0x014c)
            path.write_bytes(data)
            self.assertFalse(pe_x64(path))


    def test_auditor_never_follows_redirect_with_token(self):
        """A malicious local API must not forward the auditor's Bearer token."""
        received = []

        class Target(BaseHTTPRequestHandler):
            def do_GET(self):
                received.append(self.headers.get("Authorization"))
                body = b'{"stolen":true}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        target = ThreadingHTTPServer(("127.0.0.1", 0), Target)

        class Source(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/ok":
                    body = b'{"status":"ok"}'
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(302)
                    self.send_header(
                        "Location", "http://127.0.0.1:%d/leak" % target.server_port
                    )
                    self.end_headers()

            def log_message(self, *args):
                pass

        source = ThreadingHTTPServer(("127.0.0.1", 0), Source)
        servers = (source, target)
        threads = [threading.Thread(target=srv.serve_forever, daemon=True)
                   for srv in servers]
        for thread in threads:
            thread.start()
        try:
            base = "http://127.0.0.1:%d" % source.server_port
            self.assertEqual(
                api_json(base + "/redirect", token="audit-private-token"),
                {"_error": "HTTPError"},
            )
            self.assertEqual(received, [], "Audit token leaked via HTTP redirect")
            self.assertEqual(
                api_json(base + "/ok", token="audit-private-token"),
                {"status": "ok"},
            )
        finally:
            for srv in servers:
                srv.shutdown()
                srv.server_close()
            for thread in threads:
                thread.join(timeout=3)

    def test_scoring_and_safety(self):
        with self.assertRaises(ValueError):
            local_url("http://192.168.76.99:8787")
        with self.assertRaises(ValueError):
            local_url("http://user:password@localhost:8787")
        self.assertEqual(local_url("http://127.0.0.1:8787"), "http://127.0.0.1:8787")
        metrics = dict.fromkeys(("files","unreadable","py_checked","py_bad",
             "json_bad","mcp_bad","symlinks"), 0)
        score, tests = score_checks(Path.cwd(), metrics, {
            "health": False, "auth": False, "models": False, "chat": False
        }, False)
        self.assertLess(score, 100)
        text = markdown(Path.cwd(), {**dict.fromkeys((
            "files","dirs","bytes","hashed","hash_skipped","private","heavy",
            "thirdparty","py_checked","py_bad","json_checked","json_bad",
            "mcp","mcp_bad","unreadable","symlinks"),0)}, [], {
            "health_info":"unreachable","auth":False,
            "models":False,"model_count":0,"chat_info":"no probado"
        }, score, tests, "No encontrado")
        self.assertIn("No representa el porcentaje real", text)
        self.assertIn("MORLET", "MORLET")
if __name__ == "__main__":
    unittest.main()
