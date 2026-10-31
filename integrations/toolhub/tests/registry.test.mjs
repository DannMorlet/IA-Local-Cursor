import test from 'node:test';
import assert from 'node:assert/strict';
import { validateRegistry, getEnabledEntry, allowTool } from '../src/registry.mjs';

function registry(enabled = false) {
  return {
    mcpServers: {
      joystick: {
        enabled, transport: 'stdio', command: 'python',
        args: ['C:/Matick/server.py'], allowedTools: ['gemco_status'],
      },
    },
  };
}

test('requiere activación explícita y permisos por herramienta', () => {
  const doc = validateRegistry(registry());
  assert.throws(() => getEnabledEntry(doc, 'joystick'), /deshabilitado/);
  const prev = process.env.MATICK_MCP_EXEC_ENABLED;
  process.env.MATICK_MCP_EXEC_ENABLED = '1';
  try {
    const enabled = validateRegistry(registry(true));
    const entry = getEnabledEntry(enabled, 'joystick');
    assert.throws(() => allowTool(entry, 'no_autorizada', true), /fuera/);
    assert.throws(() => allowTool(entry, 'gemco_status', true), /desarmadas/);
  } finally {
    if (prev === undefined) delete process.env.MATICK_MCP_EXEC_ENABLED;
    else process.env.MATICK_MCP_EXEC_ENABLED = prev;
  }
});

test('rechaza comandos shell y ejecución inline', () => {
  const bad = registry(true);
  bad.mcpServers.joystick.command = 'powershell.exe';
  assert.throws(() => validateRegistry(bad), /Python\/Node/);
  bad.mcpServers.joystick.command = 'node';
  bad.mcpServers.joystick.args = ['-e', 'process.exit(0)'];
  assert.throws(() => validateRegistry(bad), /inline/);
});

test('rechaza omitir enabled o allowedTools', () => {
  const bad = registry();
  delete bad.mcpServers.joystick.enabled;
  assert.throws(() => validateRegistry(bad), /enabled/);
});
