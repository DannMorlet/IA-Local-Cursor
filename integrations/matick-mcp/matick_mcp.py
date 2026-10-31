#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Matick MCP Bridge v1: herramienta ORIGINAL, solo biblioteca estándar.

Puede ser consumida por hosts MCP compatibles (incluido LM Studio), pero no
contiene código, SDK, pesos o nombres de marca de un proveedor externo.
El servidor Matick debe estar encendido; sin permiso explícito solo lee.
"""
from __future__ import annotations

import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

VERSION = "1.0.0"
MAX_INPUT = 65536
MAX_OUTPUT = 131072
PROTOCOL = "2025-03-26"
ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")


class BridgeError(Exception):
    pass


class RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BridgeError("El servidor devolvió una redirección no permitida")


def get_base_url():
    base = os.environ.get("MATICK_CLOUD_URL", "http://127.0.0.1:8787").rstrip("/")
    uri = urlsplit(base)
    if (uri.scheme not in ("http", "https") or not uri.hostname or uri.username
            or uri.password or uri.query or uri.fragment or uri.path not in ("", "/")):
        raise BridgeError("MATICK_CLOUD_URL inválida")
    if uri.scheme == "http" and uri.hostname.lower() not in ("localhost", "127.0.0.1", "::1"):
        raise BridgeError("MATICK_CLOUD_URL requiere HTTPS para servicios remotos")
    return base


def matick_request(path, body=None, *, public=False):
    # Las rutas están codificadas en este servidor; no aceptar URLs del modelo.
    if path not in ("/health", "/v1/status", "/v1/capabilities",
                    "/v1/models", "/v1/tasks", "/v1/chat"):
        raise BridgeError("Ruta Matick desconocida")
    if path == "/v1/tasks" and body is not None and not (
        os.environ.get("MATICK_MCP_ALLOW_TASK_CREATE") == "1"
    ):
        raise BridgeError("Crear tareas requiere MATICK_MCP_ALLOW_TASK_CREATE=1")
    if path == "/v1/chat" and os.environ.get("MATICK_MCP_ALLOW_CHAT") != "1":
        raise BridgeError("Enviar conversaciones requiere MATICK_MCP_ALLOW_CHAT=1")
    token = os.environ.get("MATICK_TOKEN", "")
    if not public and not token:
        raise BridgeError("MATICK_TOKEN no está configurado en el proceso MCP")
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token and not public:
        if "\r" in token or "\n" in token:
            raise BridgeError("MATICK_TOKEN inválido")
        headers["Authorization"] = "Bearer " + token
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    if data is not None and len(data) > 12000:
        raise BridgeError("Petición demasiado grande")
    req = Request(get_base_url() + path, data=data, headers=headers,
                  method="POST" if data is not None else "GET")
    try:
        with build_opener(RejectRedirect()).open(req, timeout=8) as response:
            blob = response.read(MAX_OUTPUT + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        # No incluir URL ni cuerpo de error, que podrían contener datos sensibles.
        raise BridgeError("No se pudo consultar la API Matick autenticada") from exc
    if len(blob) > MAX_OUTPUT:
        raise BridgeError("La respuesta de Matick excedió el límite de seguridad")
    try:
        value = json.loads(blob)
    except (ValueError, UnicodeError) as exc:
        raise BridgeError("Matick devolvió JSON inválido") from exc
    return value


TOOLS = [
    {
        "name": "matick_health",
        "description": "Consulta el estado básico del servidor Matick (solo lectura).",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "matick_capabilities",
        "description": "Lee las capacidades realmente configuradas del Matick propio.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "matick_models",
        "description": "Lista los modelos reportados por Matick, sin cargar ni descargar archivos.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "matick_tasks",
        "description": "Consulta las tareas del tablero Matick (solo lectura).",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "matick_create_task",
        "description": "Crea una tarea en Matick solo con permiso local explícito.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 120},
                "detail": {"type": "string", "maxLength": 2000},
            },
            "required": ["title"],
            "additionalProperties": False,
        },
    },
    {
        "name": "matick_ask",
        "description": "Pregunta al motor de inferencia CONFIGURADO en Matick; requiere permiso explícito.",
        "inputSchema": {
            "type": "object",
            "properties": {"prompt": {"type": "string", "minLength": 1, "maxLength": 4000}},
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
]


def no_args(arguments):
    if arguments != {}:
        raise BridgeError("Esta herramienta no acepta argumentos")


def call_tool(name, arguments):
    if not isinstance(arguments, dict):
        raise BridgeError("Los argumentos deben ser un objeto JSON")
    if name == "matick_health":
        no_args(arguments)
        return matick_request("/health", public=True)
    if name == "matick_capabilities":
        no_args(arguments)
        return matick_request("/v1/capabilities")
    if name == "matick_models":
        no_args(arguments)
        return matick_request("/v1/models")
    if name == "matick_tasks":
        no_args(arguments)
        return matick_request("/v1/tasks")
    if name == "matick_create_task":
        if set(arguments) - {"title", "detail"}:
            raise BridgeError("Argumentos desconocidos")
        title, detail = arguments.get("title"), arguments.get("detail", "")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
            raise BridgeError("El título debe tener entre 1 y 120 caracteres")
        if not isinstance(detail, str) or len(detail) > 2000:
            raise BridgeError("La descripción supera el límite")
        return matick_request("/v1/tasks", {"title": title, "detail": detail})
    if name == "matick_ask":
        if set(arguments) != {"prompt"}:
            raise BridgeError("La pregunta requiere únicamente prompt")
        prompt = arguments.get("prompt")
        if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 4000:
            raise BridgeError("La pregunta debe tener entre 1 y 4000 caracteres")
        return matick_request("/v1/chat", {
            "messages": [{"role": "user", "content": prompt}],
        })
    raise BridgeError("Herramienta Matick desconocida")


def dispatch(message):
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return {"error": {"code": -32600, "message": "Solicitud JSON-RPC inválida"}}
    method = message.get("method")
    if method == "initialize":
        return {"result": {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "matick-studio-mcp", "version": VERSION},
        }}
    if method == "ping":
        return {"result": {}}
    if method == "tools/list":
        return {"result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params", {})
        if not isinstance(params, dict):
            return {"error": {"code": -32602, "message": "Parámetros inválidos"}}
        try:
            payload = call_tool(params.get("name"), params.get("arguments", {}))
            return {"result": {"content": [
                {"type": "text", "text": json.dumps(payload, ensure_ascii=False)},
            ], "isError": False}}
        except BridgeError as exc:
            return {"result": {
                "content": [{"type": "text", "text": str(exc)}],
                "isError": True,
            }}
    if method == "notifications/initialized" or (
        isinstance(method, str) and method.startswith("notifications/")
    ):
        return None
    return {"error": {"code": -32601, "message": "Método no implementado"}}


def serve(stdin=sys.stdin, stdout=sys.stdout):
    for raw in stdin:
        if len(raw) > MAX_INPUT:
            continue
        try:
            request = json.loads(raw)
            if not isinstance(request, dict):
                continue
            # Las notificaciones no deben responder.
            if "id" not in request:
                continue
            result = dispatch(request)
            if result is None:
                continue
            if "id" in request:
                result["jsonrpc"] = "2.0"
                result["id"] = request["id"]
            stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
            stdout.flush()
        except (ValueError, TypeError, BrokenPipeError):
            continue


if __name__ == "__main__":
    serve()
