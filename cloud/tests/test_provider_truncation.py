"""Regression: provider must never silently clip generated text."""
import io
import json
import unittest
from matick_cloud.provider import OpenAICompatibleProvider


class FakeResponse:
    def __init__(self, content):
        self.body = io.BytesIO(json.dumps({"choices": [{"message": {"content": content}}]}).encode())
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, count):
        return self.body.read(count)


class FakeOpener:
    def __init__(self, content):
        self.content = content
    def open(self, req, timeout):
        return FakeResponse(self.content)


class ProviderTruncationTests(unittest.TestCase):
    def test_long_reply_is_visibly_marked(self):
        provider = OpenAICompatibleProvider("http://127.0.0.1:1234", "test")
        provider.opener = FakeOpener("a" * 12050)
        response = provider.respond([{"role": "user", "content": "hola"}])
        self.assertTrue(response["stats"]["output_truncated"])
        self.assertIn("Respuesta recortada", response["content"])
        self.assertLessEqual(len(response["content"]), 12050)

    def test_short_reply_is_unchanged(self):
        provider = OpenAICompatibleProvider("http://127.0.0.1:1234", "test")
        provider.opener = FakeOpener("respuesta completa")
        response = provider.respond([{"role": "user", "content": "hola"}])
        self.assertEqual(response["content"], "respuesta completa")
        self.assertNotIn("output_truncated", response["stats"])


if __name__ == "__main__":
    unittest.main()
