"""Pruebas del diagnostico local, sin acceso a PC ni red."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from diagnostico_matick_pc_v1 import diagnose, write_report, WEIGHTS


class DiagnosisTests(unittest.TestCase):
    def test_weights_cover_100(self):
        self.assertEqual(sum(WEIGHTS.values()), 100)

    def test_inventory_and_report_are_readonly(self):
        with TemporaryDirectory() as temp:
            root = Path(temp) / "Matick"
            root.mkdir()
            (root / "cloud/matick_cloud").mkdir(parents=True)
            (root / "cloud/matick_cloud/server.py").write_text("x=1\n", encoding="utf8")
            (root / "config.example.json").write_text('{"mcpServers": {}}', encoding="utf8")
            (root / "mcp.json").write_text('{"env":{"TOKEN":"PRIVADO"}}', encoding="utf8")
            (root / "cuda").mkdir()
            (root / "cuda" / "big.bin").write_bytes(b"1234")
            info, inventory = diagnose(root)
            self.assertEqual(info["resumen"]["archivos_totales"], 4)
            self.assertEqual(info["resumen"]["archivos_sensibles_no_leidos"], 1)
            self.assertEqual(info["resumen"]["terceros_o_pesados"], 1)
            self.assertIn(info["puntaje_preparacion"], range(1, 101))
            self.assertTrue(any(x["estado"] == "SIN_PROBAR" for x in info["checks"]))
            self.assertNotIn("PRIVADO", json.dumps(info))
            outside = Path(temp) / "Downloads"
            path = write_report(info, inventory, outside, root)
            self.assertTrue(path.is_file())
            self.assertTrue((outside / "Matick_Inventario_Completo.json").is_file())
            self.assertTrue((root / "mcp.json").is_file())

    def test_refuse_report_inside_project(self):
        with TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            (root / "a.py").write_text("print(1)")
            report, inventory = diagnose(root)
            with self.assertRaises(ValueError):
                write_report(report, inventory, root / "reports", root)


if __name__ == "__main__":
    unittest.main()
