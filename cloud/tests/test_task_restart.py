"""Regresión de persistencia de tareas al reiniciar el servidor Cloud."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen

from matick_cloud.server import EventStore, MatickHTTPServer


TOKEN = "windows-0123456789-token-valid"


class TaskRestartTests(unittest.TestCase):
    def test_task_survives_server_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "tasks.sqlite"

            def start():
                server = MatickHTTPServer(
                    ("127.0.0.1", 0), EventStore(database),
                    {"windows-dx12": TOKEN})
                thread = threading.Thread(
                    target=server.serve_forever, daemon=True)
                thread.start()
                return server, thread

            def request(server, path, payload=None):
                body = json.dumps(payload).encode() if payload is not None else None
                req = Request(
                    f"http://127.0.0.1:{server.server_port}{path}",
                    data=body,
                    headers={"Authorization": f"Bearer {TOKEN}"},
                    method="POST" if body is not None else "GET")
                with urlopen(req, timeout=5) as response:
                    return json.load(response)

            server, thread = start()
            try:
                created = request(server, "/v1/tasks", {
                    "title": "Persistir después del reinicio",
                    "detail": "No perder tareas de Matick Work"})
                request(server, "/v1/tasks/status", {
                    "id": created["id"], "status": "doing"})
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

            server, thread = start()
            try:
                tasks = request(server, "/v1/tasks")["tasks"]
                matches = [task for task in tasks if task["id"] == created["id"]]
                self.assertEqual(len(matches), 1)
                self.assertEqual(matches[0]["title"], created["title"])
                self.assertEqual(matches[0]["status"], "doing")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
