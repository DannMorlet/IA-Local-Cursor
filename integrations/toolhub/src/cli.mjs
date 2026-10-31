import { createLmStudioAdapter } from './lmstudio.mjs';
import { loadRegistry } from './registry.mjs';
import { withMcpServer } from './mcp-stdio.mjs';

async function main() {
  const [task, ...args] = process.argv.slice(2);
  if (task === 'models' || task === 'chat') {
    const adapter = await createLmStudioAdapter();
    const output = task === 'models'
      ? await adapter.listModels()
      : await adapter.respond(args[0], args[1]);
    console.log(JSON.stringify(output, null, 2));
    return;
  }
  if (task === 'mcp:list') {
    const registry = await loadRegistry();
    console.log(JSON.stringify(Object.entries(registry.mcpServers).map(([name, server]) => ({
      name, enabled: server.enabled,
      allowedTools: server.allowedTools,
    })), null, 2));
    return;
  }
  if (task === 'mcp:tools' || task === 'mcp:call') {
    const registry = await loadRegistry();
    const [name, tool, rawArgs] = args;
    if (!name) throw new Error('Especifica el servidor MCP');
    const output = await withMcpServer(registry, name, async client => (
      task === 'mcp:tools'
        ? client.listTools()
        : client.callTool(tool, rawArgs ? JSON.parse(rawArgs) : {})
    ));
    console.log(JSON.stringify(output, null, 2));
    return;
  }
  console.log('Uso: node src/cli.mjs models | chat "hola" [modelo] | mcp:list | mcp:tools SERVIDOR | mcp:call SERVIDOR HERRAMIENTA "{...}"');
}

main().catch(error => {
  console.error('Matick ToolHub:', error.message);
  process.exitCode = 1;
});
