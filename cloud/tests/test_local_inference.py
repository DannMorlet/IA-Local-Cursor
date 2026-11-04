"""Pruebas del ciclo de vida local sin cargar modelos, red ni ejecutables."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from matick_cloud.local_inference import LlamaCppSidecar, LocalInferenceError, PORT


class LocalInferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "MatickStudioLM"
        self.engine = self.home / "engines" / "b12099-cuda13"
        self.engine.mkdir(parents=True)
        self.exe = self.engine / "llama-server.exe"
        self.exe.write_bytes(b"MZfake-just-for-test")
        self.model = Path(self.temp.name) / "test.gguf"
        self.model.write_bytes(b"GGUF" + b"test")
        self.config = self.home / "inference.json"
        self.data = {
            "enabled": True, "backend": "llama.cpp", "executable": str(self.exe),
            "model_path": str(self.model), "gpu_layers": 25, "context_size": 4096,
        }
        self.env = {"LOCALAPPDATA": self.temp.name, "MATICK_HOST": "127.0.0.1"}

    def save(self):
        self.config.write_text(json.dumps(self.data), encoding="utf-8")

    def test_no_config_no_engine(self):
        self.assertIsNone(LlamaCppSidecar.from_env(self.env))

    def test_disabled_no_engine(self):
        self.data["enabled"] = False
        self.save()
        self.assertIsNone(LlamaCppSidecar.from_env(self.env))

    def test_valid_config(self):
        self.save()
        engine = LlamaCppSidecar.from_env(self.env)
        self.assertEqual(engine.executable, self.exe)
        self.assertEqual(engine.model, self.model)
        self.assertEqual(engine.context, 4096)

    def test_preserves_user_provider(self):
        self.save()
        self.env["MATICK_MODEL_BASE_URL"] = "https://my.example.com"
        self.assertIsNone(LlamaCppSidecar.from_env(self.env))

    def test_rejects_remote_server(self):
        self.save()
        self.env["MATICK_HOST"] = "0.0.0.0"
        self.assertIsNone(LlamaCppSidecar.from_env(self.env))

    def test_rejects_non_gguf(self):
        self.model.write_bytes(b"ABCD")
        self.save()
        with self.assertRaisesRegex(LocalInferenceError, "cabecera GGUF"):
            LlamaCppSidecar.from_env(self.env)

    def test_rejects_exe_outside_home(self):
        self.data["executable"] = str(self.model)
        self.save()
        with self.assertRaises(LocalInferenceError):
            LlamaCppSidecar.from_env(self.env)

    def test_rejects_invalid_context(self):
        self.data["context_size"] = 0
        self.save()
        with self.assertRaisesRegex(LocalInferenceError, "context_size"):
            LlamaCppSidecar.from_env(self.env)

    def test_rejects_bad_json(self):
        self.config.write_text("{", encoding="utf-8")
        with self.assertRaises(LocalInferenceError):
            LlamaCppSidecar.from_env(self.env)

    def test_child_process_owned_and_env_connected(self):
        self.save()
        engine = LlamaCppSidecar.from_env(self.env)
        process = MagicMock()
        process.poll.return_value = None
        with patch("matick_cloud.local_inference.socket.socket") as sock, \
             patch("matick_cloud.local_inference.subprocess.Popen", return_value=process) as launch, \
             patch.dict(os.environ, {}, clear=False):
            sock.return_value.__enter__.return_value.connect_ex.return_value = 1
            engine.start()
            args = launch.call_args.args[0]
            self.assertEqual(args[0], str(self.exe))
            self.assertIn("127.0.0.1", args)
            self.assertIn(str(PORT), args)
            self.assertEqual(os.environ.get("MATICK_MODEL_ID"), "matick-local")
            engine.stop()
            process.terminate.assert_called_once()
            self.assertNotIn("MATICK_MODEL_ID", os.environ)

    def test_occupied_port_does_not_launch(self):
        self.save()
        engine = LlamaCppSidecar.from_env(self.env)
        with patch("matick_cloud.local_inference.socket.socket") as sock, \
             patch("matick_cloud.local_inference.subprocess.Popen") as launch:
            sock.return_value.__enter__.return_value.connect_ex.return_value = 0
            with self.assertRaisesRegex(LocalInferenceError, "ocupado"):
                engine.start()
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
