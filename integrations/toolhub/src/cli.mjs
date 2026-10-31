import {matickRequest} from './matick-api.mjs';
import {loadRegistry} from './registry.mjs';
import {withMcpServer} from './mcp-stdio.mjs';
async function main(){
  const [task,...args]=process.argv.slice(2);
  if(['models','chat','capabilities'].includes(task)){
    const response=task==='models'?await matickRequest('/v1/models')
      :task==='capabilities'?await matickRequest('/v1/capabilities')
      :await matickRequest('/v1/chat',{messages:[{role:'user',content:String(args[0]??'').trim()}]});
    console.log(JSON.stringify(response,null,2));return;
  }
  if(task==='mcp:list'){
    const registry=await loadRegistry();
    console.log(JSON.stringify(Object.entries(registry.mcpServers).map(([name,server])=>({
      name,enabled:server.enabled,allowedTools:server.allowedTools
    })),null,2));return;
  }
  if(task==='mcp:tools'||task==='mcp:call'){
    const registry=await loadRegistry(),[name,tool,raw]=args;
    if(!name)throw new Error('Falta nombre MCP');
    const response=await withMcpServer(registry,name,async client=>(
      task==='mcp:tools'?client.listTools():client.callTool(tool,raw?JSON.parse(raw):{})
    ));
    console.log(JSON.stringify(response,null,2));return;
  }
  console.log('Uso: node src/cli.mjs models | chat "hola" | capabilities | mcp:list | mcp:tools SERVIDOR');
}
main().catch(error=>{console.error('Matick ToolHub:',error.message);process.exitCode=1;});
