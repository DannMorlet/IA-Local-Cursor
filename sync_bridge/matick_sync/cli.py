"""Cliente para enviar y escuchar eventos locales de Matick Sync Bridge."""
import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


_SAFE_OPENER = build_opener(_NoRedirect())


def api(method: str, path: str, payload: dict | None = None) -> dict:
    base = os.getenv('MATICK_SYNC_URL', 'http://127.0.0.1:8788')
    # No transportar el token de puente a una dirección externa en este CLI.
    url = urlsplit(base)
    if (url.scheme != 'http' or url.hostname not in ('127.0.0.1', 'localhost') or
        url.username is not None or url.password is not None or
        url.path not in ('', '/') or url.query or url.fragment):
        raise ValueError('El CLI solo acepta una URL HTTP local exacta sin credenciales en la URL.')
    try:
        if url.port is None or not 1 <= url.port <= 65535:
            raise ValueError('Puerto local no válido')
    except ValueError:
        raise ValueError('Puerto local no válido') from None
    token = os.getenv('MATICK_SYNC_TOKEN', '')
    if len(token) < 20:
        raise ValueError('MATICK_SYNC_TOKEN ausente o demasiado corto')
    headers = {'Authorization': 'Bearer ' + token}
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None
    if body is not None:
        headers['Content-Type'] = 'application/json'
    request = Request(base + path, method=method, data=body, headers=headers)
    with _SAFE_OPENER.open(request, timeout=30) as resp:
        return json.load(resp)


def main() -> int:
    p = argparse.ArgumentParser(description='Matick Sync Bridge — cliente local')
    s = p.add_subparsers(dest='action', required=True)
    s.add_parser('status')
    send = s.add_parser('send')
    send.add_argument('recipient', choices=['all','morlet','claude','gemini','chatgpt','matick'])
    send.add_argument('text')
    send.add_argument('--client-id')
    watch = s.add_parser('watch')
    watch.add_argument('--after', type=int, default=0)
    watch.add_argument('--once', action='store_true')
    ask = s.add_parser('ask')
    ask.add_argument('prompt')
    ask.add_argument('--agents', default='gemini,claude')
    task = s.add_parser('task')
    task.add_argument('task_id')
    args = p.parse_args()
    try:
        if args.action == 'status':
            result = api('GET', '/v1/status')
        elif args.action == 'send':
            result = api('POST', '/v1/events', {
                'recipient': args.recipient, 'kind': 'message',
                'text': args.text, 'client_id': args.client_id,
            })
        elif args.action == 'ask':
            result = api('POST', '/v1/tasks', {
                'prompt': args.prompt, 'agents': args.agents.split(','),
            })
        elif args.action == 'task':
            result = api('GET', '/v1/tasks/' + args.task_id)
        else:
            after = args.after
            while True:
                result = api('GET', f'/v1/poll?after={after}&wait={0 if args.once else 20}')
                for event in result['events']:
                    print(json.dumps(event, ensure_ascii=False), flush=True)
                after = result['next_after']
                if args.once:
                    return 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, HTTPError, URLError, TimeoutError) as exc:
        if isinstance(exc, HTTPError):
            print(f'Error HTTP {exc.code} (Matick Sync)', file=sys.stderr)
        else:
            print(f'Error: {exc}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
