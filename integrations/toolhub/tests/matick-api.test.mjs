import test from 'node:test';
import assert from 'node:assert/strict';
import {matickRequest,validateMatickUrl} from '../src/matick-api.mjs';
test('Matick API sin SDK tercero y solo HTTPS remoto',()=>{
  assert.equal(validateMatickUrl('http://127.0.0.1:8787'),'http://127.0.0.1:8787');
  assert.throws(()=>validateMatickUrl('http://192.168.1.3:8787'),/HTTPS/);
  assert.throws(()=>validateMatickUrl('https://user:pass@example.com/'),/inválida/);
});
test('Token, rutas y respuesta propias',async()=>{
  const requests=[];
  const fake=async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>({models:[]})};};
  const r=await matickRequest('/v1/models',undefined,{baseUrl:'http://127.0.0.1:8787',token:'local-test',fetchImpl:fake});
  assert.deepEqual(r,{models:[]});
  assert.equal(requests[0].options.headers.Authorization,'Bearer local-test');
  await assert.rejects(()=>matickRequest('/v1/models',undefined,{baseUrl:'http://127.0.0.1:8787',token:'',fetchImpl:fake}),/TOKEN/);
  await assert.rejects(()=>matickRequest('/v1/events',undefined,{baseUrl:'http://127.0.0.1:8787',fetchImpl:fake}),/autorizada/);
});
