"""Motor local opcional llama.cpp para Matick Core (sin dependencia de LM Studio).

No descarga binarios ni modelos. Solo se inicia si la configuración local existe
y el usuario eligió explícitamente un GGUF mediante el instalador.
El proceso hijo termina al cerrar Matick Core y, en Windows, también queda
protegido por el Job Object del lanzador.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys

PORT = 18776
MODEL_ID = "matick-local"


class LocalInferenceError(RuntimeError):
    """Configuración o arranque inválido del motor local."""


class LlamaCppSidecar:
    def __init__(self, executable: Path, model: Path, home: Path, gpu_layers: int, context: int) -> None:
        self.executable = executable
        self.model = model
        self.home = home
        self.gpu_layers = gpu_layers
        self.context = context
        self.process: subprocess.Popen | None = None

    @staticmethod
    def config_path(env: dict[str, str] | None = None) -> Path | None:
        env = os.environ if env is None else env
        home = env.get("LOCALAPPDATA", "").strip()
        return Path(home) / "MatickStudioLM" / "inference.json" if home else None

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "LlamaCppSidecar | None":
        env = os.environ if env is None else env
        # Jamás sobreescribir un proveedor de inferencia elegido por el usuario.
        if (env.get("MATICK_MODEL_BASE_URL") or env.get("MATICK_MODEL_ID")
                or env.get("MATICK_REST_V1_URL")):
            return None
        # No correr un motor local junto a un servidor expuesto fuera del equipo.
        if env.get("MATICK_HOST", "127.0.0.1") not in ("127.0.0.1", "localhost", "::1"):
            return None
        path = cls.config_path(env)
        if path is None or not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise LocalInferenceError("inference.json no es un JSON válido") from exc
        if not isinstance(data, dict) or data.get("enabled") is not True:
            return None
        if data.get("backend") != "llama.cpp":
            raise LocalInferenceError("Backend local no reconocido")
        home = path.parent.resolve()
        engines = (home / "engines").resolve()
        if not isinstance(data.get("executable"), str) or not isinstance(data.get("model_path"), str):
            raise LocalInferenceError("Las rutas del motor y GGUF deben ser texto")
        exe = Path(data["executable"]).resolve()
        model = Path(data["model_path"]).resolve()
        # Restringir el ejecutable al directorio de versiones instaladas
        # por Matick, aunque el modelo GGUF sí puede estar en cualquier carpeta.
        if exe.name.lower() != "llama-server.exe" or not exe.is_relative_to(engines):
            raise LocalInferenceError("llama-server.exe debe encontrarse en la carpeta engines de Matick")
        if not exe.is_file():
            raise LocalInferenceError("No se encontró llama-server.exe")
        if model.suffix.lower() != ".gguf" or not model.is_file():
            raise LocalInferenceError("Selecciona un archivo GGUF existente")
        try:
            with model.open("rb") as stream:
                if stream.read(4) != b"GGUF":
                    raise LocalInferenceError("El archivo seleccionado no tiene cabecera GGUF")
        except OSError as exc:
            raise LocalInferenceError("No es posible leer la cabecera GGUF") from exc
        gpu = data.get("gpu_layers", 99)
        ctx = data.get("context_size", 4096)
        if type(gpu) is not int or not 0 <= gpu <= 999:
            raise LocalInferenceError("gpu_layers debe estar entre 0 y 999")
        if type(ctx) is not int or not 512 <= ctx <= 32768:
            raise LocalInferenceError("context_size debe estar entre 512 y 32768")
        return cls(exe, model, home, gpu, ctx)

    def start(self) -> None:
        if self.process is not None:
            raise LocalInferenceError("El motor ya está iniciado")
        # Evita conectarse accidentalmente a un servicio ajeno en este puerto.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.4)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                raise LocalInferenceError("El puerto local 18776 está ocupado; no se utilizará el servicio ajeno")
        log_dir = self.home / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        command = [
            str(self.executable), "--model", str(self.model),
            "--host", "127.0.0.1", "--port", str(PORT),
            "--alias", MODEL_ID, "--ctx-size", str(self.context),
            "--n-gpu-layers", str(self.gpu_layers),
        ]
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
        try:
            with (log_dir / "llama-inference.log").open("a", encoding="utf-8") as output:
                self.process = subprocess.Popen(
                    command, cwd=str(self.executable.parent),
                    stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                    creationflags=flags,
                )
        except OSError as exc:
            raise LocalInferenceError("No se pudo iniciar el motor llama.cpp") from exc
        # Indicar el proveedor local solo después de crear el proceso hijo.
        os.environ["MATICK_MODEL_BASE_URL"] = "http://127.0.0.1:%d" % PORT
        os.environ["MATICK_MODEL_ID"] = MODEL_ID

    def stop(self) -> None:
        proc, self.process = self.process, None
        if proc is None:
            return
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        # No borrar ajustes del usuario: solo nuestras variables exactas.
        if os.environ.get("MATICK_MODEL_BASE_URL") == "http://127.0.0.1:%d" % PORT:
            os.environ.pop("MATICK_MODEL_BASE_URL", None)
        if os.environ.get("MATICK_MODEL_ID") == MODEL_ID:
            os.environ.pop("MATICK_MODEL_ID", None)
