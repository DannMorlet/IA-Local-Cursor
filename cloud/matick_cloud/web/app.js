"use strict";
const $ = id => document.getElementById(id);
const state = { token:"", models:[], selected:"", loadedInstances:[], tasks:[], view:"workspace", chat:[], previousResponseId:null, conversationModel:null };
function showMessage(message) {
  $("toast").textContent = String(message);
  $("toast").classList.remove("hidden");
  window.clearTimeout(showMessage.timer);
  showMessage.timer = setTimeout(()=>$("toast").classList.add("hidden"),5500);
}
async function api(path, body=undefined) {
  if (!state.token) throw new Error("Conecta un token válido");
  const options = { method:body===undefined?"GET":"POST",
    headers:{Authorization:"Bearer "+state.token, Accept:"application/json"} };
  if (body!==undefined) { options.headers["Content-Type"]="application/json"; options.body=JSON.stringify(body); }
  let response;
  try {response=await fetch(path,options);} catch {throw new Error("El servidor Matick no está disponible");}
  let result={};
  try {result=await response.json();} catch {throw new Error("Matick devolvió una respuesta inválida");}
  if (!response.ok) throw new Error(result.error || "Error HTTP "+response.status);
  return result;
}
function view(name) {
  state.view=name;
  for(const item of document.querySelectorAll(".view"))item.classList.toggle("hidden",item.id!=="view-"+name);
  for(const item of document.querySelectorAll(".nav, .rail-button, .mode-tab")){
    const selected=item.dataset.view===name;
    item.classList.toggle("active",selected);
    if(item.classList.contains("mode-tab"))item.setAttribute("aria-pressed",String(selected));
    if(item.classList.contains("nav")||item.classList.contains("rail-button"))
      item.setAttribute("aria-current",selected?"page":"false");
  }
  $("view-name").textContent={workspace:"Trabajo",chat:"Chat",models:"Modelos IA",tools:"Herramientas MCP"}[name];
}
document.querySelectorAll("[data-view]").forEach(button=>button.addEventListener("click",()=>view(button.dataset.view)));
document.querySelectorAll("[data-go]").forEach(button=>button.addEventListener("click",()=>view(button.dataset.go)));
$("connect-button").addEventListener("click",()=>{$("login-dialog").classList.remove("hidden");$("token-input").focus();});
$("login-form").addEventListener("submit", async e=>{
  e.preventDefault();
  const token=$("token-input").value.trim();
  if(token.length<16){$("login-error").textContent="Token demasiado corto";return;}
  state.token=token;
  try {
    const capabilities=await api("/v1/capabilities");
    $("login-dialog").classList.add("hidden");
    $("token-input").value="";
    $("login-error").textContent="";
    $("status").textContent="API autenticada";
    $("connected-dot").classList.add("connected");
    $("state-api").textContent="Conectado";
    $("state-engine").textContent=capabilities.rest_v1?.configured?"REST v1 configurado":"No configurado";
    await Promise.all([refreshModels(),refreshTasks()]);
  } catch(err) {state.token="";$("login-error").textContent=err.message;}
});
function empty(element,message) {element.replaceChildren();const p=document.createElement("div");p.className="empty";p.textContent=message;element.append(p);}
async function refreshModels(){
  try {
    const [inventory,settings]=await Promise.all([api("/v1/models"),api("/v1/models/settings")]);
    state.models=Array.isArray(inventory.models)?inventory.models:[];
    $("state-engine").textContent=inventory.connected?"REST v1 disponible":"No configurado";
    $("model-count").textContent=state.models.length+" modelos";
    if(settings.model) selectModel(settings.model,true);
    setSavedSettings(settings);
    renderModels();
  }catch(err){empty($("model-list"),"Sin conexión REST v1: "+err.message);}
}
function selectModel(id, fromSettings=false) {
  if(state.selected!==id){state.chat=[];state.previousResponseId=null;state.conversationModel=null;}
  state.selected=id;
  $("model-id").value=id;
  $("model-current").textContent=id;
  $("state-model").textContent=id;
  $("model-chip").textContent=id;
  $("home-model-chip").textContent=id;
  const row=state.models.find(m=>m.key===id);
  state.loadedInstances=(row && Array.isArray(row.loaded_instances))?row.loaded_instances:[];
  if(!fromSettings) renderModels();
}
function setSavedSettings(value){
  const all={...value.generation,...value.load};
  for(const [key,val] of Object.entries(all)){
    const input=$(key);if(!input)continue;
    if(input.type==="checkbox")input.checked=Boolean(val);
    else input.value=String(val);
  }
}
function renderModels(){
  const container=$("model-list");container.replaceChildren();
  const query=$("model-search").value.toLowerCase();
  const filtered=state.models.filter(m=>(m.key+" "+m.name).toLowerCase().includes(query));
  if(!filtered.length){empty(container,"No hay modelos descargados que coincidan.");return;}
  for(const model of filtered){
    const btn=document.createElement("button");btn.className="model-row"+(state.selected===model.key?" selected":"");
    const title=document.createElement("strong");title.textContent=model.name||model.key;
    const detail=document.createElement("small");const instances=Array.isArray(model.loaded_instances)?model.loaded_instances.length:0;
    detail.textContent=model.key+" · "+(model.type||"llm")
      +(model.params_string?" · "+model.params_string:"")
      +(model.quantization?" · "+model.quantization:"")
      +(model.max_context_length?" · "+model.max_context_length+" ctx":"")
      +" · "+(instances?"Cargado":"No cargado");
    btn.append(title,detail);btn.addEventListener("click",()=>selectModel(model.key));
    container.append(btn);
  }
}
$("refresh-models").addEventListener("click",refreshModels);
$("model-search").addEventListener("input",renderModels);
function formValues(){
  const id=$("model-id").value.trim();
  const number=k=>Number($(k).value);
  const generation={temperature:number("temperature"),top_p:number("top_p"),
    top_k:number("top_k"),min_p:number("min_p"),
    repeat_penalty:number("repeat_penalty"),reasoning:$("reasoning").value,
    max_output_tokens:number("max_output_tokens")};
  if (!generation.reasoning) delete generation.reasoning;
  const load={context_length:number("context_length"),eval_batch_size:number("eval_batch_size"),
    flash_attention:$("flash_attention").checked,
    offload_kv_cache_to_gpu:$("offload_kv_cache_to_gpu").checked};
  for(const [k,min,max] of [["temperature",0,1],["top_p",0,1],["top_k",1,500],
    ["min_p",0,1],["repeat_penalty",.5,2],
    ["max_output_tokens",16,8192],["context_length",512,65536],["eval_batch_size",16,4096]]){
    const n=number(k);if(!Number.isFinite(n)||n<min||n>max)throw new Error("Parámetro "+k+" fuera de rango");
  }
  for(const k of ["top_k","max_output_tokens","context_length","eval_batch_size"]){
    if(!Number.isInteger(number(k)))throw new Error(k+" requiere número entero");
  }
  if(!id)throw new Error("Selecciona un modelo primero");
  return {model:id,generation,load};
}
async function runModel(action){
  try{
    const config=formValues();
    if(action==="save"){
      await api("/v1/models/settings",config);
      selectModel(config.model);
      showMessage("Parámetros del modelo guardados.");
    }else if(action==="load"){
      await api("/v1/models/settings",config);
      showMessage("Se solicitó cargar el modelo; comprueba RAM y VRAM.");
      await api("/v1/models/load",{model:config.model,params:config.load});
      showMessage("Modelo cargado en el motor conectado.");
      await refreshModels();
    }else if(action==="unload"){
      const instance=state.loadedInstances[0]?.id;
      if(!instance)throw new Error("Selecciona una instancia que esté cargada");
      if(!confirm("¿Liberar la instancia "+instance+" de la memoria?"))return;
      await api("/v1/models/unload",{instance_id:instance,model:config.model});
      showMessage("Se descargó la instancia de la RAM/VRAM.");
      await refreshModels();
    }
  }catch(err){showMessage(err.message);}
}
$("save-model").addEventListener("click",()=>runModel("save"));
$("load-model").addEventListener("click",()=>runModel("load"));
$("unload-model").addEventListener("click",()=>runModel("unload"));
$("download-model").addEventListener("click",async()=>{
  const id=$("download-id").value.trim();
  if(!id){showMessage("Escribe el ID del modelo del catálogo");return;}
  if(!confirm("Esto puede descargar varios GB AL SERVIDOR de modelos. ¿Continuar?"))return;
  try {const result=await api("/v1/models/download",{model:id});
    showMessage("Solicitud: "+(result.download?.status||"aceptada")+". Revisa el progreso en LM Studio.");}
  catch(err){showMessage(err.message);}
});
function chatBubble(role,text){
  const container=$("conversation");
  const welcome=container.querySelector(".welcome");if(welcome)welcome.remove();
  const p=document.createElement("div");p.className="message "+role;
  const title=document.createElement("span");title.className="byline";title.textContent=role==="user"?"TÚ":"MATICK";
  const body=document.createElement("span");body.textContent=text;p.append(title,body);
  container.append(p);container.scrollTop=container.scrollHeight;
}
// La portada envía al mismo chat real, sin crear una ruta de inferencia paralela.
$("home-form").addEventListener("submit", e=>{
  e.preventDefault();
  const prompt=$("home-prompt").value.trim();
  if(!prompt)return;
  if(!state.token){
    showMessage("Conecta tu servidor Matick para comenzar.");
    $("login-dialog").classList.remove("hidden");
    $("token-input").focus();
    return;
  }
  $("prompt").value=prompt;
  $("home-prompt").value="";
  view("chat");
  $("chat-form").requestSubmit();
});
$("home-prompt").addEventListener("keydown",e=>{
  if(e.key==="Enter" && e.ctrlKey){
    e.preventDefault();
    $("home-form").requestSubmit();
  }
});
$("home-new-task").addEventListener("click",createTask);

$("chat-form").addEventListener("submit",async e=>{
  e.preventDefault();
  const prompt=$("prompt").value.trim();if(!prompt)return;
  $("prompt").value="";state.chat.push({role:"user",content:prompt});chatBubble("user",prompt);
  $("send-chat").disabled=true;
  try {
    const stateful=$("stateful-chat").checked;
    const request={messages:state.chat.slice(-12),stateful};
    if(stateful && state.previousResponseId && state.conversationModel===state.selected)
      request.previous_response_id=state.previousResponseId;
    const response=await api("/v1/chat",request);
    chatBubble("assistant",response.content);
    state.chat.push({role:"assistant",content:response.content});
    state.previousResponseId=stateful?(response.response_id||null):null;
    state.conversationModel=state.selected;
    const stats=response.stats||{};
    const details=[];
    if(Number.isFinite(stats.tokens_per_second))
      details.push(Number(stats.tokens_per_second).toFixed(1)+" tokens/s");
    if(Number.isFinite(stats.input_tokens)) details.push(stats.input_tokens+" tokens entrada");
    if(Number.isFinite(stats.total_output_tokens)) details.push(stats.total_output_tokens+" tokens salida");
    $("chat-stats").textContent=details.join(" · ")||"Respuesta recibida";
  }catch(err){chatBubble("assistant","No se generó una respuesta: "+err.message);}
  finally{$("send-chat").disabled=false;}
});
$("prompt").addEventListener("keydown",e=>{if(e.key==="Enter" && e.ctrlKey){e.preventDefault();$("chat-form").requestSubmit();}});
$("clear-chat").addEventListener("click",()=>{
  state.chat=[];state.previousResponseId=null;state.conversationModel=null;
  $("chat-stats").textContent="Nueva conversación sin historial";
  empty($("conversation"),"Nueva conversación lista.");
});
async function refreshTasks(){
  try {
    const data=await api("/v1/tasks");state.tasks=data.tasks||[];
    const board=$("task-board"),side=$("sidebar-tasks");board.replaceChildren();side.replaceChildren();
    if(!state.tasks.length)empty(board,"No hay trabajos todavía. Crea uno para empezar.");
    for(const task of state.tasks){
      const card=document.createElement("div");card.className="task-card";
      const title=document.createElement("strong");title.textContent=task.title;
      const detail=document.createElement("small");detail.textContent=task.detail||"Sin descripción";
      const select=document.createElement("select");
      for(const [value,label] of [["todo","Por hacer"],["doing","En curso"],["done","Terminado"]]){
        const option=document.createElement("option");option.value=value;option.textContent=label;select.append(option);
      }
      select.value=task.status;
      select.addEventListener("change",async()=>{
        try{await api("/v1/tasks/status",{id:task.id,status:select.value});showMessage("Estado actualizado.");}
        catch(err){showMessage(err.message);await refreshTasks();}
      });
      card.append(title,detail,select);board.append(card);
      const link=document.createElement("button");link.textContent=task.title;link.addEventListener("click",()=>view("workspace"));side.append(link);
    }
  }catch(err){showMessage("Tareas: "+err.message);}
}
async function createTask(){
  if(!state.token){$("login-dialog").classList.remove("hidden");return;}
  const title=prompt("Nombre del nuevo trabajo:");if(!title)return;
  const detail=prompt("Descripción breve (opcional):")||"";
  try{await api("/v1/tasks",{title,detail});await refreshTasks();view("workspace");}
  catch(err){showMessage(err.message);}
}
$("new-task").addEventListener("click",createTask);
$("refresh-tasks").addEventListener("click",refreshTasks);
view("workspace");
