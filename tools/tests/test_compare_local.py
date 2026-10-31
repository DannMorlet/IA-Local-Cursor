import hashlib
import tempfile
import unittest
from pathlib import Path

from compare_local import compare, git_blob_sha, markdown, scan_local


class CompareTests(unittest.TestCase):
    def test_hash_is_git_blob_hash(self):
        content = b"abc"
        expected = hashlib.sha1(b"blob 3\x00abc").hexdigest()
        self.assertEqual(git_blob_sha(content), expected)

    def test_scan_skips_secrets_and_reads_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "main.cpp").write_text(
                "#include <d3d12.h>\nint main(){D3D12CreateDevice();}\n", encoding="utf8"
            )
            (root / "mcp.json").write_text(
                '{"mcpServers":{"private":{"env":{"TOKEN":"SECRET"}}}}',
                encoding="utf8"
            )
            (root / ".env").write_text("TOKEN=SECRET", encoding="utf8")
            (root / "models").mkdir()
            (root / "models" / "model.gguf").write_bytes(b"model-data")
            files, stats = scan_local(root)
            self.assertEqual(set(files), {"main.cpp"})
            self.assertEqual(stats["mcp_configs"], 1)
            self.assertTrue(stats["detected"]["Interfaz DirectX 12"])

    def test_compare_and_report(self):
        a = git_blob_sha(b"same")
        b = git_blob_sha(b"old")
        normalized = git_blob_sha(b"hello\n")
        local = {
            "same.py": {"sha": a, "sha_lf": a},
            "different.py": {"sha": b, "sha_lf": b},
            "crlf.cpp": {
                "sha": git_blob_sha(b"hello\r\n"), "sha_lf": normalized,
            },
            "only_local.py": {"sha": a, "sha_lf": a},
        }
        remote = {
            "same.py": {"sha": a}, "different.py": {"sha": git_blob_sha(b"new")},
            "crlf.cpp": {"sha": normalized},
            "only_remote.py": {"sha": a},
        }
        result = compare(local, remote)
        self.assertEqual(result["identicos"], ["same.py"])
        self.assertEqual(result["diferentes"], ["different.py"])
        self.assertEqual(result["solo_saltos_de_linea"], ["crlf.cpp"])
        self.assertEqual(result["solo_local"], ["only_local.py"])
        self.assertEqual(result["solo_github"], ["only_remote.py"])
        info = {
            "detected": {"MCP / JSON-RPC": False},
            "skipped": 0,
            "mcp_configs": 0,
        }
        output = markdown(Path("C:/IA/Matick Studio LM"), "DannMorlet/IA-Local-Cursor",
                          "main", "abcde", local, info, result)
        self.assertIn("Misma ruta, contenido diferente (1)", output)
        self.assertIn("solo lectura", output)
        self.assertIn("only_local.py", output)


if __name__ == "__main__":
    unittest.main()
