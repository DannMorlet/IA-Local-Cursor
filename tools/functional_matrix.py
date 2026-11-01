"""Reproducible Matick CI evidence matrix (stdlib only).

Scores are points for explicitly verified checks, NOT a percentage of all app
features. Real Windows/GPU/inference checks remain untested until performed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

# id, description, weight, CI environment variable, evidence scope
CHECKS = (
    ("api", "API, autenticación y SQLite (pruebas de contrato)", 15, "MATICK_TEST_API", "CI simulado"),
    ("chat_mock", "Chat HTTP y proveedor simulado", 10, "MATICK_TEST_CHAT", "CI simulado"),
    ("rest_mock", "Modelos REST v1 con servidor simulado", 10, "MATICK_TEST_REST", "CI simulado"),
    ("work", "Tareas y tablero Work (pruebas de contrato)", 10, "MATICK_TEST_WORK", "CI simulado"),
    ("mcp", "Protocolo MCP con servidor simulado", 5, "MATICK_TEST_MCP", "CI simulado"),
    ("web_syntax", "Sintaxis JavaScript de Matick Work", 5, "MATICK_TEST_WEB", "CI estático"),
    ("toolhub", "ToolHub y adaptadores MCP Node", 5, "MATICK_TEST_TOOLHUB", "CI simulado"),
    ("dx12_build", "Compilación Windows x64 / DirectX 12", 5, "MATICK_TEST_DX12", "CI compilación"),
    ("gdi_smoke", "Arranque GDI en runner Windows", 5, "MATICK_TEST_GDI", "CI smoke"),
    ("installer", "Instalar, arrancar API y desinstalar en runner", 10, "MATICK_TEST_INSTALLER", "CI smoke"),
    ("gpu_local", "Render DirectX 12 en RTX 5060 del usuario", 10, None, "PC real pendiente"),
    ("inference_local", "Chat con modelo real, latencia y estabilidad", 10, None, "PC real pendiente"),
)
assert sum(item[2] for item in CHECKS) == 100


def evaluate(evidence: dict[str, str]) -> dict:
    """Missing or unknown evidence is UNTESTED, never a pass."""
    states = {"success": "APROBADO", "failure": "FALLIDO"}
    checks = []
    for key, label, weight, variable, scope in CHECKS:
        raw = evidence.get(variable, "") if variable else ""
        status = states.get(raw, "SIN PROBAR")
        checks.append({"id": key, "nombre": label, "peso": weight,
                       "estado": status, "alcance": scope,
                       "evidencia": variable if raw in states else None})
    passed = sum(c["peso"] for c in checks if c["estado"] == "APROBADO")
    failed = sum(c["peso"] for c in checks if c["estado"] == "FALLIDO")
    untested = 100 - passed - failed
    return {"puntos_verificados": passed, "puntos_fallidos": failed,
            "puntos_sin_probar": untested, "cobertura_de_pruebas": passed + failed,
            "advertencia": "NO es el porcentaje real de funcionamiento de toda la aplicación.",
            "checks": checks}


def markdown(result: dict, sha: str = "", run_url: str = "") -> str:
    lines = ["# Matick Studio LM — evidencia funcional por versión", "",
             f"Commit: `{sha or 'sin identificar'}`", "",
             f"GitHub Actions: {run_url or 'sin enlace'}", "",
             f"**Puntos aprobados: {result['puntos_verificados']}/100** · "
             f"fallidos: {result['puntos_fallidos']} · "
             f"sin probar: {result['puntos_sin_probar']} · "
             f"cobertura de verificaciones: {result['cobertura_de_pruebas']}%", "",
             "**Esto NO equivale al porcentaje real de funcionamiento de la app.** "
             "Las pruebas simuladas validan contratos; compilar no demuestra renderizado real, "
             "ni un backend HTTP demuestra inferencia local.", "",
             "| Verificación | Puntos | Estado | Alcance |", "|---|---:|---|---|"]
    for c in result["checks"]:
        lines.append(f"| {c['nombre']} | {c['peso']} | {c['estado']} | {c['alcance']} |")
    lines.extend(["", "## Cómo interpretar", "",
                  "- APROBADO: hay evidencia de la prueba concreta en CI, no de todas las funciones.",
                  "- FALLIDO: la prueba concreta falló; revisar los logs del run.",
                  "- SIN PROBAR: no hay resultado verificable; no se presenta como éxito ni fallo.",
                  "- Para un porcentaje de funcionamiento real en PC faltan pruebas de GPU, "
                  "inferencia con pesos reales y flujos de uso continuado.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="out/functional-report")
    args = parser.parse_args()
    evidence = {variable: os.environ.get(variable, "")
                for _, _, _, variable, _ in CHECKS if variable}
    result = evaluate(evidence)
    result["commit"] = os.environ.get("GITHUB_SHA", "")
    result["run_url"] = os.environ.get("MATICK_RUN_URL", "")
    result["generado_utc"] = datetime.now(timezone.utc).isoformat()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "matick_funcional.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "matick_funcional.md").write_text(markdown(result, result["commit"], result["run_url"]), encoding="utf-8")
    print(f"Verificaciones aprobadas: {result['puntos_verificados']}/100; "
          f"sin probar: {result['puntos_sin_probar']}/100. NO es funcionalidad real de la app.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
