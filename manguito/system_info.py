"""Telemetría de hardware local de solo lectura.

No recopila archivos personales ni ejecuta comandos suministrados por usuarios.
El único ejecutable invocado es nvidia-smi, si está disponible.
"""
from __future__ import annotations
import platform
import subprocess


def get_system_info() -> dict:
    info: dict = {
        "operating_system": platform.system(),
        "cpu": platform.processor() or "No disponible",
        "gpu": None,
    }
    try:
        process = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
            shell=False,
        )
        if process.returncode != 0:
            return info
        lines = [line.strip() for line in process.stdout.splitlines() if line.strip()]
        if not lines:
            return info
        # No mostramos IDs de hardware, números de serie ni identificadores personales.
        items = [item.strip() for item in lines[0].split(",")]
        if len(items) != 5:
            return info
        name, usage, used, total, temp = items
        info["gpu"] = {
            "name": name[:120],
            "utilization_percent": int(usage),
            "memory_used_mb": int(used),
            "memory_total_mb": int(total),
            "temperature_celsius": int(temp) if temp.isdigit() else None,
        }
    except (FileNotFoundError, OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return info
