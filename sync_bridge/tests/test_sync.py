"""Pruebas de bridge real usando solo loopback y agentes simulados."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from matick_sync.server import Bridge, Store, load_tokens


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name) / 'events.db')
        self.tokens = {
            'morlet': 'morlet-test-012345678901234',
            'gemini': 'gemini-test-012345678901234',
            'claude': 'claude-test-012345678901234',
        }
        self.called = []

        def fake(agent, prompt):
            self.called.append((agent, prompt))
            return f'{agent.upper()}: {prompt}'

        self.srv = Bridge(('127.0.0.1', 0), self.store, self.tokens,
                          enable_api=False, max_tasks=2, responder=fake)
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
        self.base = f'http://127.0.0.1:{self.srv.server_port}'

    def stop(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.thread.join(timeout=3)

    def call(self, path, role=None, method='GET', data=None):
        headers = {}
        if role:
            headers['Authorization'] = 'Bearer ' + self.tokens[role]
        body = json.dumps(data).encode() if data is not None else None
        if body is not None:
            headers['Content-Type'] = 'application/json'
        req = Request(self.base + path, data=body, headers=headers, method=method)
        with urlopen(req, timeout=5) as resp:
            return resp.status, json.load(resp)

    def test_public_health_and_auth(self):
        code, health = self.call('/health')
        self.assertEqual(code, 200)
        self.assertEqual(health['service'], 'matick-sync-bridge')
        with self.assertRaises(HTTPError) as denied:
            self.call('/v1/status')
        self.assertEqual(denied.exception.code, 401)
        _, status = self.call('/v1/status', 'gemini')
        self.assertEqual(status['role'], 'gemini')
        self.assertFalse(status['api_dispatch_enabled'])

    def test_user_message_and_agent_isolation(self):
        code, sent = self.call('/v1/events', 'morlet', 'POST',
                               {'recipient':'gemini', 'kind':'message','text':'Hola'})
        self.assertEqual(code, 201)
        self.assertEqual(sent['source'], 'morlet')
        _, receive = self.call('/v1/poll?after=0', 'gemini')
        self.assertEqual(receive['events'][0]['text'], 'Hola')
        _, other = self.call('/v1/poll?after=0', 'claude')
        self.assertEqual(other['events'], [])
        with self.assertRaises(HTTPError) as denied:
            self.call('/v1/events', 'gemini', 'POST',
                      {'recipient':'claude','kind':'message','text':'No permitido'})
        self.assertEqual(denied.exception.code, 403)
        _, reply = self.call('/v1/events', 'gemini', 'POST',
                             {'recipient':'morlet','kind':'reply','text':'Recibido'})
        self.assertEqual(reply['source'], 'gemini')
        _, owner = self.call('/v1/poll?after=0', 'morlet')
        self.assertEqual(len(owner['events']), 2)

    def test_idempotency_and_replay(self):
        data = {'recipient': 'all', 'kind': 'message', 'text': 'mismo', 'client_id': 'abc123'}
        _, first = self.call('/v1/events', 'morlet', 'POST', data)
        _, again = self.call('/v1/events', 'morlet', 'POST', data)
        self.assertEqual(first['id'], again['id'])
        _, inbox = self.call('/v1/poll?after=0', 'morlet')
        self.assertEqual(len(inbox['events']), 1)
        reopened = Store(self.store.path)
        self.assertEqual(reopened.list_events('morlet', 0)[0]['text'], 'mismo')

    def test_long_poll_wakes_on_event(self):
        result = {}
        def listener():
            result['value'] = self.call('/v1/poll?after=0&wait=3', 'gemini')
        t = threading.Thread(target=listener)
        start = time.monotonic()
        t.start()
        time.sleep(.15)
        self.call('/v1/events', 'morlet', 'POST',
                  {'recipient':'gemini','kind':'message','text':'Aviso inmediato'})
        t.join(timeout=4)
        self.assertFalse(t.is_alive())
        self.assertLess(time.monotonic() - start, 2.6)
        self.assertEqual(result['value'][1]['events'][0]['text'], 'Aviso inmediato')

    def test_paid_calls_disabled_by_default(self):
        with self.assertRaises(HTTPError) as error:
            self.call('/v1/tasks', 'morlet', 'POST',
                      {'prompt':'Hola', 'agents':['gemini','claude']})
        self.assertEqual(error.exception.code, 409)
        self.assertEqual(self.called, [])
        with self.assertRaises(HTTPError) as permission:
            self.call('/v1/tasks', 'gemini', 'POST',
                      {'prompt':'Hola', 'agents':['gemini']})
        self.assertEqual(permission.exception.code, 403)

    def test_explicit_dispatch_with_mock_agent(self):
        self.srv.enable_api = True
        with patch('matick_sync.providers.configured', return_value=True):
            status, sent = self.call('/v1/tasks', 'morlet', 'POST',
                                     {'prompt':'Revisen el panel', 'agents':['gemini','claude']})
            self.assertEqual(status, 202)
            task_id = sent['task_id']
            for _ in range(100):
                _, task = self.call('/v1/tasks/' + task_id, 'morlet')
                if task['status'] != 'queued' and task['status'] != 'running':
                    break
                time.sleep(.03)
            self.assertEqual(task['status'], 'completed')
            self.assertEqual(set(task['result']), {'gemini','claude'})
            self.assertEqual(len(self.called), 2)
            _, messages = self.call('/v1/poll?after=0', 'morlet')
            self.assertEqual([x['kind'] for x in messages['events']].count('answer'), 2)
            with self.assertRaises(HTTPError) as cap:
                for _ in range(2):
                    self.call('/v1/tasks', 'morlet', 'POST',
                              {'prompt':'otra', 'agents':['gemini']})
            self.assertEqual(cap.exception.code, 429)

    def test_malformed_inputs_and_tokens(self):
        with self.assertRaises(HTTPError) as bad:
            self.call('/v1/events', 'morlet', 'POST',
                      {'recipient':'all','kind':'message','text':''})
        self.assertEqual(bad.exception.code, 400)
        with self.assertRaises(HTTPError) as bad:
            self.call('/v1/poll?wait=1000', 'morlet')
        self.assertEqual(bad.exception.code, 400)
        with patch.dict('os.environ', {'MATICK_SYNC_TOKEN': 'corta',
                                     'MATICK_SYNC_TOKENS_JSON': ''}):
            with self.assertRaises(ValueError):
                load_tokens()

    def test_never_bind_public_interface(self):
        with self.assertRaises(ValueError):
            Bridge(('0.0.0.0', 0), self.store, self.tokens)


if __name__ == '__main__':
    unittest.main()

class ClientSafetyTests(unittest.TestCase):
    def test_cli_rejects_host_substitution(self):
        import os
        from matick_sync.cli import api
        with patch.dict(os.environ, {
            'MATICK_SYNC_TOKEN': 'long-test-token-012345678901234',
            'MATICK_SYNC_URL': 'http://127.0.0.1:8788@evil.example.invalid'
        }):
            with self.assertRaises(ValueError):
                api('GET', '/v1/status')

    def test_cli_rejects_remote_http(self):
        import os
        from matick_sync.cli import api
        with patch.dict(os.environ, {
            'MATICK_SYNC_TOKEN': 'long-test-token-012345678901234',
            'MATICK_SYNC_URL': 'http://example.com:8788'
        }):
            with self.assertRaises(ValueError):
                api('GET', '/v1/status')

    def test_provider_requires_key_and_model_without_call(self):
        import os
        from matick_sync import providers
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(providers.ProviderError):
                providers.answer('claude', 'hola')

    def test_provider_fixed_endpoints(self):
        import os
        from matick_sync import providers
        calls = []
        def fake_post(url, headers, payload):
            calls.append((url, headers, payload))
            if '/messages' in url:
                return {'content': [{'type':'text','text':'respuesta claude'}]}
            if 'generateContent' in url:
                return {'candidates': [{'content': {'parts':[{'text':'respuesta gemini'}]}}]}
            return {'output':[{'content':[{'type':'output_text','text':'respuesta GPT'}]}]}
        values = {
            'ANTHROPIC_API_KEY':'dummy', 'CLAUDE_MODEL':'claude-valid',
            'GEMINI_API_KEY':'dummy', 'GEMINI_MODEL':'gemini-valid',
            'OPENAI_API_KEY':'dummy', 'OPENAI_MODEL':'gpt-valid'
        }
        with patch.dict(os.environ, values), patch.object(providers, '_post', fake_post):
            self.assertEqual(providers.answer('claude', 'hola'), 'respuesta claude')
            self.assertEqual(providers.answer('gemini', 'hola'), 'respuesta gemini')
            self.assertEqual(providers.answer('chatgpt', 'hola'), 'respuesta GPT')
        self.assertEqual(len(calls), 3)
        self.assertTrue(all(c[0].startswith('https://') for c in calls))
