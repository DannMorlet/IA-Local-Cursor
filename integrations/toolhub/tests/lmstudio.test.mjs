import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeSdkUrl, createLmStudioAdapter } from '../src/lmstudio.mjs';

test('websocket solo local o TLS remoto', () => {
  assert.equal(normalizeSdkUrl('ws://127.0.0.1:1234'), 'ws://127.0.0.1:1234');
  assert.equal(normalizeSdkUrl('wss://studio.example:443'), 'wss://studio.example');
  assert.throws(() => normalizeSdkUrl('http://127.0.0.1:1234'));
  assert.throws(() => normalizeSdkUrl('ws://192.168.0.20:1234'));
  assert.throws(() => normalizeSdkUrl('wss://user:pass@studio.example'));
});

test('adaptador usa SDK inyectado para modelos y chat, sin LM Studio real', async () => {
  const calls = [];
  class Client {
    constructor(options) {
      calls.push(options);
      this.llm = {
        listLoaded: async () => [{ identifier: 'gemma-matick', path: 'gemma.gguf' }],
        model: async (...args) => {
          calls.push(args);
          return { respond: async prompt => ({ content: 'eco:' + prompt }) };
        },
      };
    }
  }
  const adapter = await createLmStudioAdapter({ ClientClass: Client });
  assert.deepEqual(await adapter.listModels(), [{
    identifier: 'gemma-matick', path: 'gemma.gguf',
  }]);
  assert.deepEqual(await adapter.respond('hola', 'gemma-matick'), {
    provider: 'lmstudio-js', content: 'eco:hola',
  });
  assert.deepEqual(calls[0], { baseUrl: 'ws://127.0.0.1:1234' });
  assert.deepEqual(calls[1], ['gemma-matick']);
  await assert.rejects(() => adapter.respond(''));
});
