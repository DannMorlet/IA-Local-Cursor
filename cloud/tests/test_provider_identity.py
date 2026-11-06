"""Regression: a proxy must not mislabel a different model's answer."""
import io
import json
import unittest
from matick_cloud.provider import OpenAICompatibleProvider, ProviderResponseError


class FakeResponse:
    def __init__(self, payload):
        self.stream = io.BytesIO(json.dumps(payload).encode("utf-8"))

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, size):
        return self.stream.read(size)


class FakeOpener:
    def __init__(self, payload):
        self.payload = payload

    def open(self, request, timeout):
        return FakeResponse(self.payload)


class ProviderIdentityTests(unittest.TestCase):
    def setUp(self):
        self.provider = OpenAICompatibleProvider("http://127.0.0.1:1234", "selected-model")

    def test_mismatched_model_rejected(self):
        self.provider.opener = FakeOpener({
            "model": "unexpected-model",
            "choices": [{"message": {"content": "Respuesta de otro modelo"}}],
        })
        with self.assertRaisesRegex(ProviderResponseError, "modelo diferente"):
            self.provider.respond([{"role": "user", "content": "Hola"}])

    def test_matching_model_accepted(self):
        self.provider.opener = FakeOpener({
            "model": "selected-model",
            "choices": [{"message": {"content": "Respuesta real"}}],
        })
        self.assertEqual(
            self.provider.respond([{"role": "user", "content": "Hola"}])["content"],
            "Respuesta real",
        )

    def test_legacy_provider_without_model_field(self):
        self.provider.opener = FakeOpener({
            "choices": [{"message": {"content": "Respuesta sin campo modelo"}}],
        })
        self.assertEqual(
            self.provider.respond([{"role": "user", "content": "Hola"}])["content"],
            "Respuesta sin campo modelo",
        )


if __name__ == "__main__":
    unittest.main()
