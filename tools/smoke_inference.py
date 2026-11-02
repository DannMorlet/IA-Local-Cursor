"""Sonda optativa y de solo lectura del contrato de chat de Matick Studio LM.

No descarga pesos, no instala dependencias, no inicia modelos ni certifica
inferencia real. Ejecutar contra una instancia Matick autorizada:
  MATICK_CLOUD_URL=http://127.0.0.1:8787 MATICK_TOKEN=... python tools/smoke_inference.py
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class ProbeError(Exception):
    """Fallo de contrato sin incluir credenciales ni contenido privado."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe(base_url: str, token: str, model: str = "", timeout: float = 30.0) -> dict:
    """Comprueba una respuesta HTTP real, sin atribuirla a pesos locales."""
    url = urlsplit(base_url.strip().rstrip("/"))
    if (url.scheme not in ("http", "https") or not url.hostname
            or url.username or url.password or url.query or url.fragment
            or url.path not in ("", "/")):
        raise ProbeError("URL_INVALIDA")
    try:
        _ = url.port
    except ValueError as exc:
        raise ProbeError("URL_INVALIDA") from exc
    if url.scheme == "http" and url.hostname.lower() not in ("localhost", "127.0.0.1", "::1"):
        raise ProbeError("HTTP_SOLO_LOOPBACK")
    if not token:
        raise ProbeError("TOKEN_NO_CONFIGURADO")
    if not 0 < timeout <= 120 or not math.isfinite(timeout):
        raise ProbeError("TIMEOUT_INVALIDO")

    payload = {
        "messages": [{"role": "user", "content": "Responde brevemente: prueba Matick."}],
        "parameters": {"max_output_tokens": 64},
    }
    if model:
        payload["model"] = model
    req = Request(
        base_url.strip().rstrip("/") + "/v1/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="POST",
    )
    start = time.perf_counter()
    try:
        with build_opener(NoRedirect()).open(req, timeout=timeout) as response:
            raw = response.read(128 * 1024 + 1)
    except HTTPError as exc:
        raise ProbeError("HTTP_%d" % exc.code) from None
    except (URLError, TimeoutError, OSError) as exc:
        raise ProbeError("PROVEEDOR_NO_DISPONIBLE") from None
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    if len(raw) > 128 * 1024:
        raise ProbeError("RESPUESTA_DEMASIADO_GRANDE")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ProbeError("JSON_INVALIDO") from None
    if not isinstance(data, dict) or not isinstance(data.get("content"), str) or not data["content"].strip():
        raise ProbeError("CHAT_SIN_TEXTO")
    reported_model = data.get("model")
    if model and reported_model != model:
        raise ProbeError("MODELO_NO_COINCIDE")
    stats = data.get("stats") if isinstance(data.get("stats"), dict) else {}
    observed = {}
    for key in ("input_tokens", "total_output_tokens", "tokens_per_second"):
        value = stats.get(key)
        if type(value) in (int, float) and math.isfinite(value) and value >= 0:
            observed[key] = value
    return {
        "estado": "APROBADO_CONTRATO_HTTP",
        "inferencia_con_pesos_reales": "SIN_PROBAR",
        "motor_propio": "SIN_PROBAR",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "modelo_reportado": reported_model if isinstance(reported_model, str) else None,
        "caracteres_respuesta": len(data["content"]),
        "http_roundtrip_ms_medido": elapsed_ms,
        "metricas_reportadas_por_proveedor": observed,
        "advertencia": "Un HTTP 200 puede provenir de un simulador; verificar pesos, proceso y GPU por separado.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba HTTP optativa de Matick (sin certificar inferencia)")
    parser.add_argument("--base-url", default=os.getenv("MATICK_CLOUD_URL", "http://127.0.0.1:8787"))
    parser.add_argument("--model", default="", help="ID del modelo esperado; opcional")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    try:
        result = probe(args.base_url, os.getenv("MATICK_TOKEN", ""), args.model, args.timeout)
    except ProbeError as exc:
        print(json.dumps({"estado": "FALLIDO", "codigo": str(exc),
                          "inferencia_con_pesos_reales": "SIN_PROBAR"}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
