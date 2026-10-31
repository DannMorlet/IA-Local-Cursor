import { readFile } from 'node:fs/promises';
import { basename, isAbsolute, resolve } from 'node:path';

const ALLOWED_EXECUTABLES = new Set(['python', 'python.exe', 'py', 'py.exe', 'node', 'node.exe']);
const MAX_SERVERS = 32;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

export function validateRegistry(doc) {
  assert(doc && typeof doc === 'object' && !Array.isArray(doc), 'Registro MCP inválido');
  assert(doc.mcpServers && typeof doc.mcpServers === 'object' && !Array.isArray(doc.mcpServers),
    'Se requiere mcpServers');
  const entries = Object.entries(doc.mcpServers);
  assert(entries.length <= MAX_SERVERS, 'Demasiados servidores MCP');
  for (const [name, entry] of entries) {
    assert(/^[a-zA-Z0-9._-]{1,64}$/.test(name), 'Nombre MCP inválido');
    assert(entry && typeof entry === 'object' && !Array.isArray(entry), 'Definición MCP inválida');
    assert(entry.enabled === true || entry.enabled === false, 'enabled debe indicarse explícitamente');
    assert(entry.transport === 'stdio', 'Solo se admite stdio local en este prototipo');
    assert(typeof entry.command === 'string' && entry.command.length > 0, 'Comando inválido');
    const exe = basename(entry.command).toLowerCase();
    assert(ALLOWED_EXECUTABLES.has(exe), 'Solo se permiten lanzadores Python/Node');
    assert(Array.isArray(entry.args) && entry.args.every(x => typeof x === 'string' && x.length <= 2048),
      'args debe ser una lista de cadenas');
    assert(!entry.args.some(x => x === '-c' || x === '-e' || x === '--eval'),
      'No se permite ejecución de código inline');
    assert(!entry.cwd || (typeof entry.cwd === 'string' && isAbsolute(entry.cwd)),
      'cwd debe ser absoluto');
    assert(Array.isArray(entry.allowedTools)
      && entry.allowedTools.every(x => typeof x === 'string' && /^[a-zA-Z0-9._-]{1,100}$/.test(x)),
      'allowedTools debe ser una lista explícita');
    assert(!entry.env || (typeof entry.env === 'object' && !Array.isArray(entry.env)
      && Object.entries(entry.env).every(([key, val]) => /^[A-Z_][A-Z0-9_]*$/.test(key)
        && typeof val === 'string' && val.length <= 2048)), 'env inválido');
  }
  return doc;
}

export async function loadRegistry(path = process.env.MATICK_MCP_CONFIG || 'mcp.json') {
  return validateRegistry(JSON.parse(await readFile(resolve(path), 'utf8')));
}

export function getEnabledEntry(registry, name) {
  const entry = registry.mcpServers[name];
  if (!entry) throw new Error('Servidor MCP desconocido');
  if (entry.enabled !== true) throw new Error('Servidor MCP deshabilitado: editar configuración local');
  if (process.env.MATICK_MCP_EXEC_ENABLED !== '1') {
    throw new Error('MCP desarmado. Debes activar MATICK_MCP_EXEC_ENABLED=1 conscientemente');
  }
  return entry;
}

export function allowTool(entry, name, permitActions = false) {
  if (!entry.allowedTools.includes(name)) throw new Error('Herramienta fuera de la lista autorizada');
  if (!permitActions || process.env.MATICK_MCP_ACT_ENABLED !== '1') {
    throw new Error('Llamadas a herramientas desarmadas: requiere MATICK_MCP_ACT_ENABLED=1');
  }
}
