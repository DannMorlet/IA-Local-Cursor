"""Verifica panel web estático y tareas persistentes sin navegador externo."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from matick_cloud.server import MatickHTTPServer, EventStore


class WorkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = MatickHTTPServer(("127.0.0.1", 0),
            EventStore(Path(self.temp.name) / "db.sqlite"),
            {"windows-dx12": "windows-0123456789-token-valid",
             "matick-chat": "chat-0123456789-token-valid"})
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:%d" % self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp.cleanup()

    def call(self, path, data=None, role="windows-dx12"):
        raw = json.dumps(data).encode() if data is not None else None
        headers = {"Authorization": "Bearer "+(
            "windows-0123456789-token-valid" if role=="windows-dx12" else
            "chat-0123456789-token-valid")}
        req = Request(self.url+path,data=raw,headers=headers,method="POST" if raw else "GET")
        with urlopen(req,timeout=4) as response:
            return response, response.read()

    def test_dashboard_files_and_csp(self):
        for path, needle, media in [
            ("/app", b"Matick Studio", "text/html"),
            ("/app/app.js", b"refreshModels", "text/javascript"),
            ("/app/style.css", b".shell", "text/css"),
        ]:
            resp, data = self.call(path)
            self.assertEqual(resp.status, 200)
            self.assertIn(needle, data)
            self.assertEqual(resp.headers.get_content_type(), media)
            self.assertIn("default-src 'none'", resp.headers.get("Content-Security-Policy"))
        with self.assertRaises(HTTPError) as unknown:
            self.call("/app/../server.py")
        self.assertEqual(unknown.exception.code, 404)

    def test_create_and_update_tasks(self):
        _, data = self.call("/v1/tasks")
        self.assertEqual(json.loads(data)["tasks"],[])
        _, data = self.call("/v1/tasks",{"title":"Arreglar pantalla DX12","detail":"Comparar con Codex"})
        task = json.loads(data)
        self.assertEqual(task["status"],"todo")
        _, data=self.call("/v1/tasks/status",{"id":task["id"],"status":"doing"})
        self.assertEqual(json.loads(data)["status"],"doing")
        _, data=self.call("/v1/tasks")
        self.assertEqual(json.loads(data)["tasks"][0]["title"],"Arreglar pantalla DX12")
        self.assertEqual(json.loads(data)["tasks"][0]["status"],"doing")
        with self.assertRaises(HTTPError) as denied:
            self.call("/v1/tasks",{"title":"intruso"},role="matick-chat")
        self.assertEqual(denied.exception.code,403)


if __name__=="__main__":
    unittest.main()
