"""Motor local administrado por Matick, basado en un ejecutable llama-server de llama.cpp.

Solo modelos GGUF encontrados bajo una raíz configurada. No descarga pesos,
drivers ni ejecutables; no usa LM Studio, ni acepta rutas arbitrarias desde HTTP.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from .models import ModelError, ModelOffline, LOAD_PARAMS, valid_params
from .provider import OpenAICompatibleProvider, ProviderResponseError, ProviderUnavailable, NoRedirect


class LocalLlamaEngine:
    """Controla exactamente un proceso hijo llama-server y un modelo a la vez."""

    def __init__(self, home, models_dir=None, executable=None, enabled=True, startup_timeout=90):
        self.home = Path(home).expanduser().resolve()
        self.models_dir = Path(models_dir or self.home).expanduser().resolve()
        name = "llama-server.exe" if os.name == "nt" else "llama-server"
        self.executable = Path(executable or self.home / "engine" / name).expanduser().resolve()
        self.enabled = enabled
        self.startup_timeout = startup_timeout
        self._lock = threading.RLock()
        self._process = None
        self._model = None
        self._port = None
        self._key = None
        self._log_file = None

    @classmethod
    def from_env(cls):
        home = os.getenv("MATICK_HOME") or (
            r"C:\IA\Matick Studio LM" if os.name == "nt"
            else str(Path.home() / "Matick Studio LM")
        )
        engine_name = "llama-server.exe" if os.name == "nt" else "llama-server"
        personal_binary = Path(home) / "engine" / engine_name
        bundled_binary = Path(__file__).resolve().parents[2] / "engine" / engine_name
        binary = os.getenv("MATICK_LLAMA_SERVER") or str(
            personal_binary if personal_binary.is_file() else
            (bundled_binary if bundled_binary.is_file() else personal_binary)
        )
        mode = os.getenv("MATICK_INFERENCE_BACKEND", "auto").strip().lower()
        if mode not in ("auto", "local", "external"):
            raise ValueError("MATICK_INFERENCE_BACKEND debe ser auto, local o external")
        # Mostrar el estado de instalación del motor también si falta el binario,
        # en lugar de ocultarlo detrás de "REST v1 no configurado".
        enabled = mode != "external"
        return cls(home, os.getenv("MATICK_LOCAL_MODELS_DIR"), binary, enabled=enabled)

    @property
    def configured(self):
        return self.enabled and self.executable.is_file()

    @property
    def reason(self):
        if not self.executable.is_file():
            return "Falta llama-server en la carpeta engine; consulta la guía del motor local."
        if not self.models_dir.is_dir():
            return "Falta la carpeta de modelos GGUF; configura MATICK_LOCAL_MODELS_DIR."
        return ""

    def _files(self):
        if not self.models_dir.is_dir():
            return []
        found = []
        # rglob puede fallar mientras recorre unidades removibles o carpetas
        # inaccesibles. Conservar las entradas ya encontradas y no devolver 500.
        iterator = iter(self.models_dir.rglob("*"))
        while len(found) < 300:
            try:
                candidate = next(iterator)
            except StopIteration:
                break
            except (OSError, RuntimeError):
                # pathlib puede emitir RuntimeError ante ciclos de directorios.
                break
            if candidate.suffix.lower() != ".gguf":
                continue
            # El archivo puede desaparecer o bloquearse durante rglob/is_file/resolve.
            # Omitir solo esa entrada; nunca modificar pesos ni rutas externas.
            try:
                if not candidate.is_file():
                    continue
                path = candidate.resolve()
            except (OSError, RuntimeError):
                # Enlaces simbólicos cíclicos pueden producir RuntimeError en resolve().
                continue
            if path.is_relative_to(self.models_dir):
                found.append(path)
        return sorted(found, key=lambda p: str(p).casefold())

    @staticmethod
    def _id(path):
        return "local/" + hashlib.sha256(str(path).casefold().encode("utf-8")).hexdigest()[:20]

    def _inventory(self):
        return {self._id(p): p for p in self._files()}

    def _alive(self):
        return self._process is not None and self._process.poll() is None

    def _ready(self):
        if not self._alive() or not self._port or not self._model or not self._key:
            return False
        base = "http://127.0.0.1:%d" % self._port
        opener = build_opener(NoRedirect())
        try:
            with opener.open(base + "/health", timeout=2) as response:
                if response.status != 200 or json.load(response).get("status") != "ok":
                    return False
            req = Request(base + "/v1/models", headers={"Authorization": "Bearer " + self._key})
            with opener.open(req, timeout=2) as response:
                catalog = json.load(response)
            return isinstance(catalog, dict) and any(
                isinstance(row, dict) and row.get("id") == self._model
                for row in catalog.get("data", [])
            )
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError):
            return False

    def models(self):
        with self._lock:
            loaded = self._model if self._ready() else None
            catalog = []
            for mid, path in self._inventory().items():
                # Un GGUF puede desaparecer entre rglob() y stat() (descarga,
                # renombrado o unidad desconectada). No tumbar /v1/models.
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                catalog.append({
                    "key": mid, "name": path.stem, "type": "llm", "format": "GGUF",
                    "size_bytes": size, "source": "llama.cpp-local",
                    "loaded_instances": ([{"id": mid}] if mid == loaded else []),
                })
            return catalog

    def load(self, model, params):
        params = valid_params(params, LOAD_PARAMS)
        if not self.configured:
            raise ModelOffline(self.reason)
        if params.get("num_experts") is not None:
            raise ValueError("num_experts no está disponible en el motor llama.cpp local")
        with self._lock:
            path = self._inventory().get(model)
            if path is None:
                raise ValueError("Selecciona un GGUF disponible del catálogo local")
            if self._model == model and self._ready():
                return {"status": "loaded", "instance_id": model, "engine": "llama.cpp-local"}
            # No descargar un modelo funcional si el GGUF seleccionado desaparecio
            # entre el inventario y la carga (por ejemplo, unidad desconectada).
            try:
                if not path.is_file():
                    raise ModelOffline("El GGUF seleccionado ya no esta disponible; actualiza el catalogo")
            except OSError as exc:
                raise ModelOffline("No se puede acceder al GGUF seleccionado; verifica la unidad y permisos") from exc
            self._stop()
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            key = secrets.token_urlsafe(28)
            command = [
                str(self.executable), "--host", "127.0.0.1", "--port", str(port),
                "--model", str(path), "--alias", model, "--api-key", key,
                "--ctx-size", str(params.get("context_length", 4096)),
                "--batch-size", str(params.get("eval_batch_size", 256)),
                "--gpu-layers", "auto", "--fit", "on", "--no-webui",
            ]
            if "flash_attention" in params:
                command += ["--flash-attn", "on" if params["flash_attention"] else "off"]
            if params.get("offload_kv_cache_to_gpu") is False:
                command.append("--no-kv-offload")
            log_root = Path(os.getenv("LOCALAPPDATA") or self.home) / "MatickStudioLM" / "logs"
            log_root.mkdir(parents=True, exist_ok=True)
            log_path = log_root / "llama-inference.log"
            self._log_file = log_path.open("ab")
            try:
                self._process = subprocess.Popen(
                    command, stdin=subprocess.DEVNULL, stdout=self._log_file,
                    stderr=subprocess.STDOUT, cwd=str(self.executable.parent),
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except OSError as exc:
                self._stop()
                raise ModelOffline("No se pudo iniciar llama-server; verifica el ejecutable y sus DLL") from exc
            self._port, self._model, self._key = port, model, key
            deadline = time.monotonic() + self.startup_timeout
            while time.monotonic() < deadline:
                if self._ready():
                    return {"status": "loaded", "instance_id": model, "engine": "llama.cpp-local"}
                if not self._alive():
                    break
                time.sleep(0.5)
            self._stop()
            raise ModelOffline("llama-server no cargó el GGUF a tiempo. Revisa llama-inference.log y la VRAM disponible")

    def chat(self, model, messages, params, previous_response_id=None, stateful=False):
        if previous_response_id is not None or stateful:
            raise ValueError("El motor local usa historial del chat; desactiva la sesión REST v1")
        with self._lock:
            if model != self._model or not self._ready():
                raise ModelOffline("Este modelo no está cargado y verificado en llama.cpp")
            provider = OpenAICompatibleProvider(
                "http://127.0.0.1:%d" % self._port, model=self._model, api_key=self._key)
            try:
                reply = provider.respond(messages, params, timeout=120, llama_cpp=True)
            except ProviderUnavailable as exc:
                raise ModelOffline("El proceso de inferencia local no respondió") from exc
            except ProviderResponseError as exc:
                raise ModelError("La respuesta de llama.cpp no es válida") from exc
            reply["engine"] = "llama.cpp-local"
            reply["model_instance_id"] = self._model
            return reply

    def unload(self, instance):
        with self._lock:
            if not self._model or instance != self._model:
                raise ValueError("La instancia seleccionada ya no está cargada")
            self._stop()
            return {"status": "unloaded", "instance_id": instance}

    def _stop(self):
        proc = self._process
        self._process = self._model = self._port = self._key = None
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=4)
        if self._log_file:
            self._log_file.close()
            self._log_file = None

    def close(self):
        with self._lock:
            self._stop()
