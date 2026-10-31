import { spawn } from 'node:child_process';
import { getEnabledEntry, allowTool } from './registry.mjs';

const TIMEOUT_MS = 12000;
const MAX_RESPONSE_BYTES = 512 * 1024;

export class McpStdioClient {
  constructor(entry, spawnFn = spawn) {
    this.entry = entry;
    this.spawnFn = spawnFn;
    this.pending = new Map();
    this.sequence = 0;
    this.buffer = '';
    this.outputBytes = 0;
  }

  async start() {
    const env = {
      PATH: process.env.PATH || '',
      SystemRoot: process.env.SystemRoot || process.env.SYSTEMROOT || '',
      TEMP: process.env.TEMP || process.env.TMP || '',
      TMP: process.env.TMP || process.env.TEMP || '',
      USERPROFILE: process.env.USERPROFILE || '',
      HOME: process.env.HOME || '',
      ...this.entry.env,
    };
    this.process = this.spawnFn(this.entry.command, this.entry.args, {
      cwd: this.entry.cwd, env, shell: false, windowsHide: true,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    this.process.stdout.on('data', chunk => this.consume(chunk));
    this.process.stderr.on('data', () => {}); // Nunca registrar secretos ni datos de modelos.
    this.process.on('error', error => this.rejectAll(error));
    this.process.on('exit', () => this.rejectAll(new Error('Servidor MCP finalizado')));
    await this.send('initialize', {
      protocolVersion: '2025-03-26',
      capabilities: {},
      clientInfo: { name: 'matick-toolhub', version: '0.1.0' },
    });
    this.process.stdin.write(JSON.stringify({
      jsonrpc: '2.0', method: 'notifications/initialized',
    }) + '\n');
    return this;
  }

  consume(chunk) {
    this.outputBytes += chunk.length;
    if (this.outputBytes > MAX_RESPONSE_BYTES) {
      this.rejectAll(new Error('El servidor MCP excedió el tamaño máximo'));
      this.stop();
      return;
    }
    this.buffer += chunk.toString('utf8');
    let end;
    while ((end = this.buffer.indexOf('\n')) !== -1) {
      const line = this.buffer.slice(0, end).trim();
      this.buffer = this.buffer.slice(end + 1);
      if (!line) continue;
      let message;
      try { message = JSON.parse(line); } catch { continue; }
      if (message.id === undefined || !this.pending.has(message.id)) continue;
      const pending = this.pending.get(message.id);
      this.pending.delete(message.id);
      clearTimeout(pending.timeout);
      if (message.error) pending.reject(new Error(message.error.message || 'Error MCP'));
      else pending.resolve(message.result);
    }
  }

  send(method, params = {}) {
    if (!this.process || !this.process.stdin.writable) {
      return Promise.reject(new Error('Servidor MCP no disponible'));
    }
    const id = ++this.sequence;
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error('Tiempo de espera MCP excedido'));
      }, TIMEOUT_MS);
      this.pending.set(id, { resolve, reject, timeout });
      this.process.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
    });
  }

  rejectAll(error) {
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timeout);
      pending.reject(error);
    }
    this.pending.clear();
  }

  async listTools() {
    const response = await this.send('tools/list');
    return (response?.tools || []).map(tool => ({
      name: tool.name, description: tool.description ?? '',
      authorized: this.entry.allowedTools.includes(tool.name),
    }));
  }

  async callTool(name, args = {}) {
    allowTool(this.entry, name, true);
    if (!args || typeof args !== 'object' || Array.isArray(args)) {
      throw new Error('arguments debe ser objeto JSON');
    }
    return this.send('tools/call', { name, arguments: args });
  }

  stop() {
    this.rejectAll(new Error('Servidor MCP detenido'));
    if (this.process && !this.process.killed) this.process.kill();
  }
}

export async function withMcpServer(registry, name, fn) {
  const entry = getEnabledEntry(registry, name);
  const client = new McpStdioClient(entry);
  try {
    await client.start();
    return await fn(client);
  } finally {
    client.stop();
  }
}
