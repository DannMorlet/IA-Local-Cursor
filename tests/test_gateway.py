import tempfile
import unittest
from pathlib import Path

from manguito.gateway import AccessDenied, Manguito, safe_path


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "hello.txt").write_text("hola\n", encoding="utf-8")
        self.app = Manguito(self.root, "a" * 40, "http://127.0.0.1:1234/v1")

    def tearDown(self):
        self.temp.cleanup()

    def test_read_and_list(self):
        self.assertEqual(self.app.read_text("hello.txt")["text"], "hola\n")
        self.assertIn("hello.txt", [e["name"] for e in self.app.list_files()["entries"]])

    def test_reject_escape_and_secrets(self):
        for name in ("../escape", ".env", ".git/config", "key.pem", "/etc/passwd"):
            with self.assertRaises(AccessDenied):
                safe_path(self.app.workspace, name)

    def test_token_is_required(self):
        self.assertFalse(self.app.authenticate(""))
        self.assertTrue(self.app.authenticate("a" * 40))

    def test_writes_disabled_by_default(self):
        p = self.app.propose("hello.txt", "cambio\n")
        self.assertIn("-hola", p["diff"])
        with self.assertRaises(AccessDenied):
            self.app.apply(p["proposal_id"], self.app.approval_code)

    def test_local_approval_and_conflict_detection(self):
        self.app.writes = True
        proposal = self.app.propose("hello.txt", "nuevo\n")
        with self.assertRaises(AccessDenied):
            self.app.apply(proposal["proposal_id"], "incorrecto")
        result = self.app.apply(proposal["proposal_id"], self.app.approval_code)
        self.assertTrue(result["saved"])
        self.assertEqual((self.root / "hello.txt").read_text(), "nuevo\n")
        old = self.app.propose("hello.txt", "futuro\n")
        (self.root / "hello.txt").write_text("otro\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.app.apply(old["proposal_id"], self.app.approval_code)

    def test_bad_message(self):
        with self.assertRaises(ValueError):
            self.app.chat([{"role": "tool", "content": "sudo"}], "example")


if __name__ == "__main__":
    unittest.main()
