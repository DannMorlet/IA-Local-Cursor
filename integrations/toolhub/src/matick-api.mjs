const ALLOWED=new Set(['/health','/v1/capabilities','/v1/models','/v1/chat','/v1/tasks']);
export function validateMatickUrl(value='http://127.0.0.1:8787'){
  const url=new URL(value);
  if(!['http:','https:'].includes(url.protocol)||url.username||url.password||url.search||url.hash||url.pathname!=='/')
    throw new Error('MATICK_CLOUD_URL inválida');
  if(url.protocol==='http:'&&!['127.0.0.1','localhost','[::1]'].includes(url.hostname))
    throw new Error('Matick remoto exige HTTPS');
  return url.origin;
}
export async function matickRequest(path,data,options={}){
  if(!ALLOWED.has(path))throw new Error('Ruta Matick no autorizada');
  const origin=validateMatickUrl(options.baseUrl||process.env.MATICK_CLOUD_URL);
  const token=options.token===undefined?process.env.MATICK_TOKEN:options.token;
  if(path!=='/health'&&!token)throw new Error('MATICK_TOKEN requerido');
  const headers={Accept:'application/json'};
  if(path!=='/health')headers.Authorization='Bearer '+token;
  const opts={headers,redirect:'error',signal:AbortSignal.timeout(20000)};
  if(data!==undefined){
    opts.method='POST';headers['Content-Type']='application/json';opts.body=JSON.stringify(data);
    if(opts.body.length>12000)throw new Error('Petición demasiado grande');
  }
  const result=await (options.fetchImpl||fetch)(origin+path,opts);
  if(!result.ok)throw new Error('Matick devolvió HTTP '+result.status);
  return result.json();
}
