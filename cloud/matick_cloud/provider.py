"""Proveedor mínimo de chat compatible con OpenAI.

No incluye pesos, CUDA, drivers ni dependencias externas. Se conecta por HTTP
a un servidor de inferencia administrado por el usuario.
"""
from __future__ import annotations

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .models import PARAMS, valid_params


class ProviderUnavailable(Exception):
    """Proveedor no configurado o temporalmente inaccesible."""


class ProviderResponseError(Exception):
    """El proveedor devolvió un resultado inválido."""


class NoRedirect(HTTPRedirectHandler):
    """Never forward a chat request or API key to a redirect destination."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # urllib normally follows POST -> GET on 301/302/303, forwarding Authorization.
        # Returning None makes the opener raise HTTPError instead.
        return None


class OpenAICompatibleProvider:
    def __init__(self, base_url: str = "", model: str = "", api_key: str = "") -> None:
        self.model = model.strip()
        self.api_key = api_key
        self.opener = build_opener(NoRedirect())
        self.base_url = base_url.strip().rstrip("/")
        if self.base_url:
            url = urlsplit(self.base_url)
            if (
                url.scheme not in ("http", "https")
                or not url.hostname or url.username or url.password
                or url.query or url.fragment
                or url.path not in ("", "/v1")
            ):
                raise ValueError("MATICK_MODEL_BASE_URL debe terminar opcionalmente en /v1 y no tener credenciales")
            # urlsplit() does not validate the port until .port is accessed.
            # Reject malformed/out-of-range ports at configuration time, not
            # during a chat request where they could become an HTTP 500.
            try:
                _ = url.port
            except ValueError as exc:
                raise ValueError("MATICK_MODEL_BASE_URL contiene un puerto inválido") from exc
            if url.scheme == "http" and url.hostname.lower() not in ("localhost", "127.0.0.1", "::1"):
                raise ValueError("El proveedor remoto requiere HTTPS")
            if url.scheme == "https" and not self.api_key:
                raise ValueError("Proveedor HTTPS requiere MATICK_MODEL_API_KEY")
        if self.model and not self.base_url:
            raise ValueError("MATICK_MODEL_ID requiere MATICK_MODEL_BASE_URL")

    @classmethod
    def from_env(cls) -> "OpenAICompatibleProvider":
        return cls(
            os.environ.get("MATICK_MODEL_BASE_URL", ""),
            os.environ.get("MATICK_MODEL_ID", ""),
            os.environ.get("MATICK_MODEL_API_KEY", ""),
        )

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.model)

    def respond(self, messages: list[dict[str, str]], params: dict | None = None) -> dict[str, object]:
        if not self.configured:
            raise ProviderUnavailable("No hay un modelo configurado en Matick Cloud")
        # OpenAI-compatible no garantiza top_k, min_p, repeat_penalty ni reasoning.
        # Solo reenviar opciones estándar; nunca fingir que se aplicaron las demás.
        options = valid_params(params if params is not None else {}, PARAMS)
        forwarded = {key: options[key] for key in ("temperature", "top_p") if key in options}
        if "max_output_tokens" in options:
            forwarded["max_tokens"] = options["max_output_tokens"]
        not_forwarded = sorted(set(options) - {"temperature", "top_p", "max_output_tokens"})
        url = self.base_url + ("" if self.base_url.endswith("/v1") else "/v1") + "/chat/completions"
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Eres Matick Studio LM. Responde en español mexicano de forma útil y concisa. No afirmes que herramientas o dispositivos están conectados sin evidencia."},
                *messages,
            ],
            "max_tokens": 512,
            **forwarded,
            "stream": False,
        }, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        req = Request(url, data=payload, headers=headers, method="POST")
        started = time.perf_counter()
        try:
            with self.opener.open(req, timeout=25) as response:
                raw = response.read(128 * 1024 + 1)
            http_roundtrip_ms = round((time.perf_counter() - started) * 1000, 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            # No divulgar URL, tokens ni cuerpo de error de proveedores externos.
            raise ProviderUnavailable("No fue posible consultar el proveedor de IA configurado") from exc
        if len(raw) > 128 * 1024:
            raise ProviderResponseError("Respuesta del proveedor demasiado grande")
        try:
            result = json.loads(raw)
            content = result["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError("Respuesta inválida del proveedor") from exc
        if not isinstance(content, str) or not content.strip():
            # HTTP 200 con contenido vacío no es una inferencia completada.
            raise ProviderResponseError("Respuesta del proveedor sin texto")
        # El tiempo incluye transporte HTTP, no es velocidad de decodificación.
        stats = {"http_roundtrip_ms": http_roundtrip_ms}
        usage = result.get("usage") if isinstance(result, dict) else None
        if isinstance(usage, dict):
            for source, target in (("prompt_tokens", "input_tokens"),
                                   ("completion_tokens", "total_output_tokens")):
                count = usage.get(source)
                # JavaScript chat clients cannot represent larger integers exactly.
                if type(count) is int and 0 <= count <= (1 << 53) - 1:
                    stats[target] = count
        # Never silently present a shortened answer as complete inference.
        # The client can surface this flag and offer a retry with fewer tokens.
        truncated = len(content) > 12000
        if truncated:
            stats["output_truncated"] = True
        return {
            "model": self.model,
            "content": content[:12000],
            "stats": stats,
            "parameters_forwarded": sorted(forwarded),
            "parameters_not_forwarded": not_forwarded,
        }
