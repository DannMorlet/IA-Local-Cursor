"""Regresiones portables del catálogo GGUF (Windows y Linux, sin llama-server)."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from matick_cloud.models import ModelOffline

from matick_cloud.local_engine import LocalLlamaEngine


class PortableInventoryTests(TestCase):
    def test_disappearing_file_during_scan_preserves_healthy_gguf(self):
        with TemporaryDirectory(prefix="Matick Studio LM ") as temp:
            root = Path(temp)
            models_dir = root / "models"
            models_dir.mkdir()
            healthy = models_dir / "modelo sano.gguf"
            healthy.write_bytes(b"GGUF-keep")
            vanishing = models_dir / "modelo retirado.gguf"
            vanishing.write_bytes(b"GGUF-temporary")
            engine = LocalLlamaEngine(root, models_dir=models_dir)
            original_is_file = Path.is_file

            def simulate_removed(path):
                if path == vanishing:
                    raise FileNotFoundError("desaparecio durante el escaneo")
                return original_is_file(path)

            with patch.object(Path, "is_file", simulate_removed):
                catalog = engine.models()

            self.assertEqual([item["name"] for item in catalog], ["modelo sano"])
            self.assertEqual(healthy.read_bytes(), b"GGUF-keep")
            self.assertEqual(vanishing.read_bytes(), b"GGUF-temporary")

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


class LoadPreflightTests(TestCase):
    def test_missing_selected_gguf_does_not_unload_existing_model(self):
        with TemporaryDirectory(prefix="Matick Studio LM ") as temp:
            root = Path(temp)
            engine_dir = root / "engine"
            engine_dir.mkdir()
            binary = engine_dir / "llama-server.exe"
            binary.write_bytes(b"fake executable: not run")
            engine = LocalLlamaEngine(root, executable=binary)
            missing = root / "models" / "missing.gguf"
            missing.parent.mkdir()
            missing_key = engine._id(missing)
            engine._model = "local/existing"
            with patch.object(engine, "_inventory", return_value={missing_key: missing}), \
                 patch.object(engine, "_ready", return_value=False), \
                 patch.object(engine, "_stop") as stop:
                with self.assertRaisesRegex(ModelOffline, "ya no esta disponible"):
                    engine.load(missing_key, {})
                stop.assert_not_called()
                self.assertEqual(engine._model, "local/existing")

    def test_unreadable_selected_gguf_preserves_existing_model(self):
        with TemporaryDirectory(prefix="Matick Studio LM ") as temp:
            root = Path(temp)
            engine_dir = root / "engine"
            engine_dir.mkdir()
            binary = engine_dir / "llama-server.exe"
            binary.write_bytes(b"fake executable: not run")
            engine = LocalLlamaEngine(root, executable=binary)
            selected = root / "models" / "locked.gguf"
            selected.parent.mkdir()
            key = engine._id(selected)
            engine._model = "local/existing"
            original_is_file = Path.is_file
            def deny(path):
                if path == selected:
                    raise PermissionError("unidad inaccesible")
                return original_is_file(path)
            with patch.object(engine, "_inventory", return_value={key: selected}), \
                 patch.object(engine, "_ready", return_value=False), \
                 patch.object(engine, "_stop") as stop, \
                 patch.object(Path, "is_file", deny):
                with self.assertRaisesRegex(ModelOffline, "No se puede acceder"):
                    engine.load(key, {})
                stop.assert_not_called()
                self.assertEqual(engine._model, "local/existing")
