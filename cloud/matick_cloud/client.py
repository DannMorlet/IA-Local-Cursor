"""CLI de prueba para el bus Matick Studio LM Cloud.

Uso:
  python -m matick_cloud.client send matick-chat mensaje '{"texto":"hola"}'
  python -m matick_cloud.client direct matick-chat matick-reloj aviso '{"texto":"revisar tarea"}'
  python -m matick_cloud.client inbox --after 0
  python -m matick_cloud.client status
  python -m matick_cloud.client routes
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def request(method: str, path: str, payload: dict | None = None) -> dict:
    base = os.environ.get("MATICK_CLOUD_URL", "http://127.0.0.1:8787").rstrip("/")
    token = os.environ.get("MATICK_TOKEN", "")
    if not token:
        raise ValueError("Define MATICK_TOKEN con el secreto de tu propio rol")
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = Request(
        base + path, data=data, method=method,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    with urlopen(req, timeout=10) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cliente de eventos Matick Studio LM")
    commands = parser.add_subparsers(dest="command", required=True)
    send = commands.add_parser("send", help="Enviar evento a otro rol")
    send.add_argument("target")
    send.add_argument("kind")
    send.add_argument("payload_json", help="Objeto JSON de datos")
    direct = commands.add_parser("direct", help="Dirigir el mismo evento a varios roles explícitos")
    direct.add_argument("targets", nargs="+", help="Roles destino; no admite comodines")
    direct.add_argument("kind")
    direct.add_argument("payload_json", help="Objeto JSON de datos")
    inbox = commands.add_parser("inbox", help="Leer eventos para el rol del token")
    inbox.add_argument("--after", type=int, default=0)
    inbox.add_argument("--limit", type=int, default=50)
    commands.add_parser("status", help="Estado de la identidad autenticada")
    commands.add_parser("routes", help="Destinos permitidos para el rol autenticado")
    args = parser.parse_args()
    try:
        if args.command == "send":
            data = json.loads(args.payload_json)
            if not isinstance(data, dict):
                raise ValueError("payload_json debe ser un objeto JSON")
            result = request("POST", "/v1/events", {
                "target": args.target, "kind": args.kind, "payload": data,
            })
        elif args.command == "direct":
            data = json.loads(args.payload_json)
            if not isinstance(data, dict):
                raise ValueError("payload_json debe ser un objeto JSON")
            result = request("POST", "/v1/direct", {
                "targets": args.targets, "kind": args.kind, "payload": data,
            })
        elif args.command == "inbox":
            result = request("GET", "/v1/events?" + urlencode({
                "after": args.after, "limit": args.limit,
            }))
        elif args.command == "status":
            result = request("GET", "/v1/status")
        else:
            result = request("GET", "/v1/routes")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, HTTPError, URLError) as exc:
        print("Error del cliente Matick: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

