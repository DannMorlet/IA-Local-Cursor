"""Adaptadores de IA optativos. No comparten sesiones ChatGPT/Gemini Live/Claude Code."""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        # Las credenciales del proveedor nunca viajan a un host redirigido.
        return None


_SAFE_OPENER = build_opener(_NoRedirect())
MAX_RESPONSE_BYTES = 1_048_576
ALLOWED = frozenset({'claude', 'gemini', 'chatgpt'})


class ProviderError(RuntimeError):
    """Error sin claves ni cuerpos de respuestas sensibles."""


def configured(agent: str) -> bool:
    key, model = {
        'claude': ('ANTHROPIC_API_KEY', 'CLAUDE_MODEL'),
        'gemini': ('GEMINI_API_KEY', 'GEMINI_MODEL'),
        'chatgpt': ('OPENAI_API_KEY', 'OPENAI_MODEL'),
    }[agent]
    return bool(os.environ.get(key) and os.environ.get(model))


def _post(url: str, headers: dict[str, str], payload: dict) -> dict:
    # URLs son literales de los proveedores: no admitimos destinos arbitrarios.
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = Request(url, data=body, method='POST', headers={
        'Content-Type': 'application/json', **headers,
    })
    try:
        with _SAFE_OPENER.open(req, timeout=45) as res:
            raw = res.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ProviderError('Respuesta demasiado grande')
            return json.loads(raw)
    except HTTPError as exc:
        # No incluir cuerpo: algunos errores muestran parte del contenido enviado.
        raise ProviderError(f'Proveedor devolvió HTTP {exc.code}') from None
    except (URLError, TimeoutError, OSError):
        raise ProviderError('Fallo de red o tiempo de espera del proveedor') from None
    except (UnicodeError, json.JSONDecodeError, ValueError):
        raise ProviderError('Respuesta no válida del proveedor') from None


def answer(agent: str, prompt: str) -> str:
    """Una llamada, sin herramientas, reintentos ni conversaciones autónomas en bucle."""
    if agent not in ALLOWED:
        raise ProviderError('Agente desconocido')
    if not configured(agent):
        raise ProviderError('Falta API key o modelo configurado para este agente')
    system = ('Eres parte de Matick Studio LM Cloud. Responde en español. '
              'Distingue hechos, planes y pasos no ejecutados. No declares acceso a '
              'archivos, PC ni GitHub sin herramientas reales.')
    if agent == 'claude':
        data = _post('https://api.anthropic.com/v1/messages', {
            'x-api-key': os.environ['ANTHROPIC_API_KEY'],
            'anthropic-version': '2023-06-01',
        }, {
            'model': os.environ['CLAUDE_MODEL'], 'max_tokens': 700,
            'system': system,
            'messages': [{'role': 'user', 'content': prompt}],
        })
        texts = [p.get('text', '') for p in data.get('content', []) if p.get('type') == 'text']
    elif agent == 'gemini':
        model = os.environ['GEMINI_MODEL']
        if not model.replace('-', '').replace('.', '').replace('_', '').isalnum():
            raise ProviderError('Nombre de modelo Gemini inválido')
        data = _post('https://generativelanguage.googleapis.com/v1beta/models/' + model + ':generateContent', {
            'x-goog-api-key': os.environ['GEMINI_API_KEY'],
        }, {
            'systemInstruction': {'parts': [{'text': system}]},
            'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
            'generationConfig': {'maxOutputTokens': 700},
        })
        texts = [p.get('text', '') for c in data.get('candidates', [])
                 for p in c.get('content', {}).get('parts', []) if 'text' in p]
    else:
        data = _post('https://api.openai.com/v1/responses', {
            'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'],
        }, {
            'model': os.environ['OPENAI_MODEL'],
            'instructions': system, 'input': prompt,
            'max_output_tokens': 700,
            'store': False,
        })
        texts = [v.get('text', '') for out in data.get('output', [])
                 for v in out.get('content', []) if v.get('type') == 'output_text']
    output = '\n'.join(t for t in texts if isinstance(t, str) and t.strip()).strip()
    if not output:
        raise ProviderError('Proveedor no devolvió texto utilizable')
    return output[:8000]
