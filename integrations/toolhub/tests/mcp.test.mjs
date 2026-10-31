import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { McpStdioClient } from '../src/mcp-stdio.mjs';

test('conversa con un MCP stdio simulado y limita llamadas', async () => {
  const folder = await mkdtemp(join(tmpdir(), 'matick-mcp-test-'));
  const script = join(folder, 'fixture.mjs');
  await writeFile(script, `
    process.stdin.setEncoding('utf8');
    let buf = '';
    process.stdin.on('data', data => {
      buf += data;
      let pos;
      while ((pos = buf.indexOf('\\n')) >= 0) {
        const line = buf.slice(0, pos); buf = buf.slice(pos + 1);
        const x = JSON.parse(line);
        if (x.id === undefined) continue;
        const result = x.method === 'initialize' ? { protocolVersion:'2025-03-26' }
          : x.method === 'tools/list' ? { tools:[{name:'echo',description:'prueba'}] }
          : { content:[{type:'text',text:String(x.params.arguments.text)}] };
        process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:x.id,result})+'\\n');
      }
    });
  `, 'utf8');
  const entry = {
    enabled: true, transport: 'stdio', command: process.execPath,
    args: [script], allowedTools: ['echo'],
  };
  const client = new McpStdioClient(entry);
  const old = process.env.MATICK_MCP_ACT_ENABLED;
  try {
    await client.start();
    assert.deepEqual(await client.listTools(), [{
      name: 'echo', description: 'prueba', authorized: true,
    }]);
    await assert.rejects(() => client.callTool('echo', { text: 'hola' }), /desarmadas/);
    process.env.MATICK_MCP_ACT_ENABLED = '1';
    await assert.rejects(() => client.callTool('shell', {}), /lista autorizada/);
    const answer = await client.callTool('echo', { text: 'hola' });
    assert.equal(answer.content[0].text, 'hola');
  } finally {
    client.stop();
    if (old === undefined) delete process.env.MATICK_MCP_ACT_ENABLED;
    else process.env.MATICK_MCP_ACT_ENABLED = old;
    await rm(folder, { recursive: true, force: true });
  }
});
