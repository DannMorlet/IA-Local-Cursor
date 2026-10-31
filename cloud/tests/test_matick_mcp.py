"""Pruebas propias del servidor MCP Matick, sin SDK de otros productos."""
import importlib.util
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading

script = Path(__file__).resolve().parents[2]/"integrations"/"matick-mcp"/"matick_mcp.py"
spec = importlib.util.spec_from_file_location("matick_mcp", script)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class MatickMock(BaseHTTPRequestHandler):
    def reply(self, value):
        data = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if self.path == "/health": self.reply({"status": "ok"})
        elif self.headers.get("Authorization") != "Bearer test-token":
            self.send_error(401)
        elif self.path == "/v1/models": self.reply({"models": []})
        elif self.path == "/v1/capabilities": self.reply({"chat": {"configured": False}})
        elif self.path == "/v1/tasks": self.reply({"tasks": []})
        else: self.send_error(404)
    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        if self.headers.get("Authorization") != "Bearer test-token":
            self.send_error(401)
        elif self.path == "/v1/tasks": self.reply({"id": 1, "title": data["title"]})
        elif self.path == "/v1/chat":
            self.reply({"content": "Respuesta " + data["messages"][0]["content"]})
        else: self.send_error(404)
    def log_message(self, *args): pass


class MatickMcpTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MatickMock)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.env = patch.dict(os.environ, {
            "MATICK_CLOUD_URL": "http://127.0.0.1:%d" % self.server.server_port,
            "MATICK_TOKEN": "test-token"
        })
        self.env.start()
        os.environ.pop("MATICK_MCP_ALLOW_CHAT", None)
        os.environ.pop("MATICK_MCP_ALLOW_TASK_CREATE", None)
    def tearDown(self):
        self.env.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def test_initialize_and_catalog(self):
        greeting = bridge.dispatch({"jsonrpc": "2.0", "method": "initialize", "params": {}})
        self.assertEqual(greeting["result"]["serverInfo"]["name"], "matick-studio-mcp")
        tools = bridge.dispatch({"jsonrpc": "2.0", "method": "tools/list"})["result"]["tools"]
        self.assertEqual(len(tools), 6)
        self.assertIn("matick_models", [x["name"] for x in tools])

    def test_stdio_jsonrpc(self):
        commands = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "matick_health", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "matick_models", "arguments": {}}},
        ]
        output = io.StringIO()
        bridge.serve(io.StringIO("".join(json.dumps(x)+"\n" for x in commands)), output)
        replies = [json.loads(x) for x in output.getvalue().splitlines()]
        self.assertEqual([x["id"] for x in replies], [1, 2, 3])
        self.assertEqual(json.loads(replies[-1]["result"]["content"][0]["text"]), {"models": []})
        self.assertNotIn("test-token", output.getvalue())

    def test_explicit_permissions_and_safe_names(self):
        with self.assertRaises(bridge.BridgeError):
            bridge.call_tool("matick_create_task", {"title": "Nueva tarea"})
        with self.assertRaises(bridge.BridgeError):
            bridge.call_tool("matick_ask", {"prompt": "hola"})
        with self.assertRaises(bridge.BridgeError):
            bridge.call_tool("execute_shell", {"command": "whoami"})
        with patch.dict(os.environ, {
            "MATICK_MCP_ALLOW_CHAT": "1",
            "MATICK_MCP_ALLOW_TASK_CREATE": "1"
        }):
            self.assertEqual(bridge.call_tool("matick_create_task", {"title": "Nueva tarea"})["id"], 1)
            self.assertEqual(bridge.call_tool("matick_ask", {"prompt": "hola"})["content"],
                             "Respuesta hola")

    def test_http_remote_without_tls_refused(self):
        with patch.dict(os.environ, {"MATICK_CLOUD_URL": "http://192.168.0.5:8787"}):
            with self.assertRaises(bridge.BridgeError):
                bridge.get_base_url()


if __name__ == "__main__":
    unittest.main()
