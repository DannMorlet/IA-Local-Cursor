"""Puente REST v1 para LM Studio y gestor de perfiles Matick sin pesos ni SDK.

LM Studio es solo un proveedor opcional: Matick conserva API, interfaz y
persistencia independientes. Redirecciones HTTP bloqueadas para el upstream.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import re
import sqlite3
import threading
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MODEL_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._/:-]{0,191}$")
PARAMS = {
    "temperature": ("float", 0, 1),
    "top_p": ("float", 0, 1),
    "top_k": ("int", 1, 500),
    "min_p": ("float", 0, 1),
    "repeat_penalty": ("float", 0.5, 2),
    "max_output_tokens": ("int", 16, 8192),
    "context_length": ("int", 512, 65536),
    "reasoning": ("choice", None, None),
}
LOAD_PARAMS = {
    "context_length": ("int", 512, 65536),
    "eval_batch_size": ("int", 16, 4096),
    "num_experts": ("int", 1, 512),
    "flash_attention": ("bool", None, None),
    "offload_kv_cache_to_gpu": ("bool", None, None),
}


class ModelError(Exception):
    pass


class ModelOffline(ModelError):
    pass


def valid_model_id(text):
    if not isinstance(text, str) or not MODEL_ID.fullmatch(text):
        raise ValueError("ID de modelo inválido")
    return text


def valid_params(value, schema):
    if not isinstance(value, dict) or set(value) - set(schema):
        raise ValueError("Parámetros desconocidos o inválidos")
    clean = {}
    for k, v in value.items():
        kind, lo, hi = schema[k]
        if kind == "bool":
            if type(v) is not bool:
                raise ValueError("El parámetro %s requiere booleano" % k)
        elif kind == "choice":
            if v not in ("off", "low", "medium", "high", "on"):
                raise ValueError("Valor reasoning no admitido")
        elif kind == "int":
            if type(v) is not int or not lo <= v <= hi:
                raise ValueError("Parámetro %s fuera de rango" % k)
        else:
            if type(v) not in (int, float) or not math.isfinite(v) or not lo <= v <= hi:
                raise ValueError("Parámetro %s fuera de rango" % k)
        clean[k] = v
    return clean


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ModelError("El proveedor intentó redirigir la petición")


class RestV1Bridge:
    def __init__(self, base_url="", token=""):
        self.base_url = base_url.rstrip("/")
        self.token = token
        if self.base_url:
            parts = urlsplit(self.base_url)
            if (parts.scheme not in ("http", "https") or not parts.hostname
                or parts.path not in ("", "/") or parts.query or parts.fragment
                or parts.username or parts.password):
                raise ValueError("MATICK_REST_V1_URL inválida")
            if parts.scheme == "http" and parts.hostname.lower() not in ("localhost", "127.0.0.1", "::1"):
                raise ValueError("REST v1 remoto requiere HTTPS")
            if parts.scheme == "https" and not token:
                raise ValueError("REST v1 externo necesita MATICK_REST_V1_TOKEN")
        self.opener = build_opener(NoRedirect())

    @classmethod
    def from_env(cls):
        return cls(os.environ.get("MATICK_REST_V1_URL", ""),
                   os.environ.get("MATICK_REST_V1_TOKEN", ""))

    @property
    def configured(self):
        return bool(self.base_url)

    def request(self, path, body=None):
        if not self.configured:
            raise ModelOffline("REST v1 no está configurado")
        if path not in ("/api/v1/models", "/api/v1/models/load",
                        "/api/v1/models/unload", "/api/v1/models/download",
                        "/api/v1/chat"):
            raise ValueError("Ruta REST v1 no permitida")
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        raw = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf8")
        req = Request(self.base_url + path, data=raw,
                      method="POST" if body is not None else "GET", headers=headers)
        try:
            with self.opener.open(req, timeout=60 if path.endswith("load") else 25) as resp:
                if resp.status >= 400:
                    raise ModelOffline("El proveedor rechazó la petición")
                result = resp.read(128 * 1024 + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise ModelOffline("REST v1 no responde o rechazó la solicitud") from exc
        if len(result) > 128 * 1024:
            raise ModelError("Respuesta REST v1 demasiado grande")
        try:
            return json.loads(result)
        except ValueError as exc:
            raise ModelError("Respuesta REST v1 inválida") from exc

    def models(self):
        result = self.request("/api/v1/models")
        models = result.get("models") if isinstance(result, dict) else None
        if not isinstance(models, list):
            raise ModelError("La lista REST v1 no contiene modelos")
        return [
            {"key": row.get("key"), "name": row.get("display_name"),
             "type": row.get("type"), "size_bytes": row.get("size_bytes"),
             "quantization": (row.get("quantization") or {}).get("name")
               if isinstance(row.get("quantization"), dict) else None,
             "loaded_instances": row.get("loaded_instances", [])}
            for row in models[:300]
            if isinstance(row, dict) and isinstance(row.get("key"), str)
        ]

    def load(self, model, params):
        keys = {row["key"] for row in self.models()}
        if model not in keys:
            raise ValueError("Selecciona un modelo disponible antes de cargarlo")
        data = {"model": valid_model_id(model), "echo_load_config": True}
        data.update(valid_params(params, LOAD_PARAMS))
        return self.request("/api/v1/models/load", data)

    def unload(self, instance):
        valid_model_id(instance)
        return self.request("/api/v1/models/unload", {"instance_id": instance})

    def download(self, model, quantization=None):
        # Descargas solo con consentimiento explícito y bandera activada en servidor.
        if os.getenv("MATICK_ALLOW_MODEL_DOWNLOADS") != "1":
            raise PermissionError("Descargas desactivadas por seguridad y espacio")
        valid_model_id(model)
        req = {"model": model}
        if quantization is not None:
            if not isinstance(quantization, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,24}", quantization):
                raise ValueError("Cuantización inválida")
            req["quantization"] = quantization
        return self.request("/api/v1/models/download", req)

    def chat(self, model, messages, params):
        valid_model_id(model)
        options = valid_params(params, PARAMS)
        prompt = "\n".join("%s: %s" % (m["role"], m["content"]) for m in messages)
        payload = {
            "model": model, "input": prompt, "stream": False, "store": False,
            "system_prompt": "Eres Matick Studio LM. Sé útil, cuidadoso y no inventes integraciones.",
            **options,
        }
        result = self.request("/api/v1/chat", payload)
        texts = [item.get("content", "") for item in result.get("output", [])
                 if isinstance(item, dict) and item.get("type") == "message"
                 and isinstance(item.get("content"), str)]
        if not texts:
            raise ModelError("El modelo no devolvió texto de respuesta")
        return {"model": model, "content": "\n".join(texts)[:12000],
                "stats": result.get("stats", {})}


class ModelState:
    """Configuración pequeña persistente, modelo seleccionado y ajustes de generación."""
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS model_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)")

    def get(self):
        with self.lock, sqlite3.connect(self.path) as db:
            value = db.execute("SELECT value FROM model_state WHERE key='active'").fetchone()
        return json.loads(value[0]) if value else {"model": None, "generation": {}, "load": {}}

    def set(self, data):
        if not isinstance(data, dict) or set(data) - {"model", "generation", "load"}:
            raise ValueError("Configuración de modelo inválida")
        previous = self.get()
        if "model" in data:
            previous["model"] = valid_model_id(data["model"]) if data["model"] is not None else None
        if "generation" in data:
            previous["generation"] = valid_params(data["generation"], PARAMS)
        if "load" in data:
            previous["load"] = valid_params(data["load"], LOAD_PARAMS)
        with self.lock, sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO model_state(key,value) VALUES('active',?)",
                       (json.dumps(previous, ensure_ascii=False),))
        return previous
