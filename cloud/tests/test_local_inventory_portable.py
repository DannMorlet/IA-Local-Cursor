"""Regresiones portables del catálogo GGUF (Windows y Linux, sin llama-server)."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from matick_cloud.local_engine import LocalLlamaEngine


class PortableInventoryTests(TestCase):
    def test_removed_and_inaccessible_gguf_do_not_hide_valid_models(self):
        with TemporaryDirectory(prefix="Matick Studio LM ") as temp:
            home = Path(temp)
            models_dir = home / "models"
            models_dir.mkdir()
            healthy = models_dir / "modelo mexicano.gguf"
            healthy.write_bytes(b"GGUF-preserve")
            missing = models_dir / "retirado.gguf"
            inaccessible = models_dir / "sin-permiso.gguf"
            engine = LocalLlamaEngine(home, models_dir=models_dir)
            original_stat = Path.stat

            def simulate_stat_failure(path, *args, **kwargs):
                if path == missing:
                    raise FileNotFoundError("modelo retirado")
                if path == inaccessible:
                    raise PermissionError("modelo temporalmente bloqueado")
                return original_stat(path, *args, **kwargs)

            with patch.object(engine, "_inventory", return_value={
                engine._id(missing): missing,
                engine._id(inaccessible): inaccessible,
                engine._id(healthy): healthy,
            }), patch.object(Path, "stat", simulate_stat_failure):
                catalog = engine.models()

            self.assertEqual(len(catalog), 1)
            self.assertEqual(catalog[0]["key"], engine._id(healthy))
            self.assertEqual(catalog[0]["size_bytes"], len(b"GGUF-preserve"))
            self.assertEqual(catalog[0]["loaded_instances"], [])
            self.assertEqual(healthy.read_bytes(), b"GGUF-preserve")
            self.assertFalse(missing.exists())
            self.assertFalse(inaccessible.exists())
