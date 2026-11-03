import {CLAIRE_STATES,frameCoordinates,normalizeSpeechText,clamp,chooseSpanishVoice} from "./clare_behavior.mjs";

const $=id=>document.getElementById(id);
const dock=$("clare-widget");
const sprite=$("clare-sprite");
const fallback=$("clare-fallback");
const status=$("clare-status");
const message=$("clare-message");
const toggle=$("clare-toggle");
const prefersReduced=window.matchMedia("(prefers-reduced-motion: reduce)");
let atlasUrl=null;
let atlasReady=false;
let animation="idle";
let frame=0;
let duration=0;
let direction=1;
let spriteX=0;
let dragging=null;
let activeUtterance=null;
let liveVisible=true;

function sayStatus(value){ status.textContent=value; }
function chatMessage(value){ message.textContent=value; }
function renderFrame(){
  if(!atlasReady) return;
  const data=frameCoordinates(animation,frame,112);
  sprite.style.width=data.width;
  sprite.style.height=data.height;
  sprite.style.backgroundSize=data.backgroundSize;
  sprite.style.backgroundPosition=data.backgroundPosition;
  sprite.style.transform="translateX("+spriteX.toFixed(1)+"px)";
}
function animate(name){
  animation=CLAIRE_STATES[name]?name:"idle";
  frame=0;
  duration=CLAIRE_STATES[animation].frames;
  renderFrame();
}
function tick(){
  if(!atlasReady||document.hidden||prefersReduced.matches)return;
  frame++;
  if(duration>0){
    duration--;
    if(animation==="running-right"||animation==="running-left"){
      spriteX=clamp(spriteX+direction*7,-65,65);
    }
    if(duration===0) {
      animation="idle";
      spriteX=0;
    }
  } else if(frame%90===0) {
    animation="waving";
    duration=CLAIRE_STATES.waving.frames;
  }
  renderFrame();
}
const timer=setInterval(tick,155);
window.addEventListener("pagehide",()=>{
  clearInterval(timer);
  if(activeUtterance && window.speechSynthesis) speechSynthesis.cancel();
  if(atlasUrl?.startsWith("blob:")) URL.revokeObjectURL(atlasUrl);
});
function setVisible(visible){
  liveVisible=Boolean(visible);
  dock.hidden=!liveVisible;
  toggle.setAttribute("aria-pressed",String(liveVisible));
  toggle.setAttribute("aria-label",liveVisible?"Ocultar Mini Clare":"Mostrar Mini Clare");
  if(liveVisible) animate("waving");
}
toggle.addEventListener("click",()=>setVisible(!liveVisible));
$("clare-close").addEventListener("click",()=>setVisible(false));
$("clare-wave").addEventListener("click",()=>{
  animate("waving");
  chatMessage("¡Hola! 🐾 Aquí estoy acompañándote en Matick.");
});
$("clare-jump").addEventListener("click",()=>{
  animate("jumping");
  chatMessage("¡Yuju! 🐾 Estoy brincando.");
});
$("clare-walk").addEventListener("click",()=>{
  direction=spriteX<0?1:-1;
  if(Math.abs(spriteX)<2)direction=1;
  animate(direction>0?"running-right":"running-left");
  duration=12;
  chatMessage("¡Voy de paseo por tu pantalla! 🐾");
});
function speak(value){
  const text=normalizeSpeechText(value,500);
  if(!text){sayStatus("Escribe algo para que Clare lo diga.");return false;}
  if(!window.speechSynthesis||!window.SpeechSynthesisUtterance) {
    sayStatus("La voz no está disponible en este navegador. Clare puede moverse y escribir.");
    return false;
  }
  try {
    speechSynthesis.cancel();
    const utterance=new SpeechSynthesisUtterance(text);
    utterance.lang="es-MX";
    utterance.rate=1.0;
    utterance.pitch=1.1;
    const voice=chooseSpanishVoice(speechSynthesis.getVoices());
    if(voice)utterance.voice=voice;
    utterance.onstart=()=>{animate("waving");sayStatus("Clare está hablando…");};
    utterance.onend=()=>{activeUtterance=null;sayStatus("Lista para hablar.");animate("idle");};
    utterance.onerror=()=>{activeUtterance=null;sayStatus("No se pudo reproducir la voz. Revisa el audio de Windows.");};
    activeUtterance=utterance;
    chatMessage(text);
    speechSynthesis.speak(utterance);
    return true;
  }catch {
    sayStatus("El sintetizador de voz no pudo iniciarse.");
    return false;
  }
}
$("clare-speak").addEventListener("click",()=>speak($("clare-text").value));
$("clare-stop-voice").addEventListener("click",()=>{
  if(window.speechSynthesis)speechSynthesis.cancel();
  activeUtterance=null;
  sayStatus("Voz detenida.");
});
$("clare-autoread").addEventListener("change",()=>{
  sayStatus($("clare-autoread").checked?
    "Leeré las respuestas del chat cuando el navegador permita voz.":
    "Lectura automática desactivada.");
});
window.addEventListener("matick:assistant-message",event=>{
  const reply=normalizeSpeechText(event.detail?.text,500);
  if(!reply)return;
  chatMessage(reply.slice(0,175)+(reply.length>175?"…":""));
  animate("waving");
  if($("clare-autoread").checked && liveVisible)speak(reply);
});
// Sin subir archivos privados a Matick Cloud: todo queda en el navegador o en la carpeta Drive sincronizada.
function dbOpen(){
  return new Promise((resolve,reject)=>{
    if(!window.indexedDB){reject(new Error("Almacenamiento local no disponible"));return;}
    const request=indexedDB.open("MatickMiniClareLocal",1);
    request.onupgradeneeded=()=>{
      if(!request.result.objectStoreNames.contains("assets"))
        request.result.createObjectStore("assets");
    };
    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error);
  });
}
async function dbRead(){
  const db=await dbOpen();
  try{
    return await new Promise((resolve,reject)=>{
      const tx=db.transaction("assets","readonly");
      const req=tx.objectStore("assets").get("spritesheet-extended");
      req.onsuccess=()=>resolve(req.result||null);
      req.onerror=()=>reject(req.error);
    });
  }finally{db.close();}
}
async function dbWrite(file){
  const db=await dbOpen();
  try{
    await new Promise((resolve,reject)=>{
      const tx=db.transaction("assets","readwrite");
      tx.objectStore("assets").put(file,"spritesheet-extended");
      tx.oncomplete=()=>resolve();
      tx.onerror=()=>reject(tx.error);
      tx.onabort=()=>reject(tx.error);
    });
  }finally{db.close();}
}
function imageCheck(src){
  return new Promise((resolve,reject)=>{
    const image=new Image();
    image.onload=()=>{
      if(image.naturalWidth===1536&&image.naturalHeight===2288)resolve(src);
      else reject(new Error("El atlas debe medir 1536 × 2288 píxeles."));
    };
    image.onerror=()=>reject(new Error("No se pudo cargar el atlas de Mini Clare."));
    image.src=src;
  });
}
async function useAtlas(src){
  await imageCheck(src);
  if(atlasUrl?.startsWith("blob:"))URL.revokeObjectURL(atlasUrl);
  atlasUrl=src;
  atlasReady=true;
  fallback.hidden=true;
  sprite.style.backgroundImage='url("'+src+'")';
  animate("waving");
  sayStatus("Mini Clare original cargada. 🐾");
}
async function restoreAtlas(){
  // La ruta /app/clare/spritesheet-extended.png solo sirve el archivo sincronizado en ESTA PC.
  try{await useAtlas("/app/clare/spritesheet-extended.png");return;}catch {}
  try{
    const blob=await dbRead();
    if(blob){
      const url=URL.createObjectURL(blob);
      try{await useAtlas(url);return;}
      catch(error){URL.revokeObjectURL(url);throw error;}
    }
  }catch {}
  sayStatus("Clare está lista. Importa su atlas original de Drive para verla animada.");
}
$("clare-import").addEventListener("click",()=>$("clare-file").click());
$("clare-file").addEventListener("change",async()=>{
  const file=$("clare-file").files?.[0];
  if(!file)return;
  $("clare-file").value="";
  if(file.type!=="image/png"||file.size>8*1024*1024){
    sayStatus("Elige spritesheet-extended.png (PNG de hasta 8 MB).");
    return;
  }
  const url=URL.createObjectURL(file);
  try{
    await useAtlas(url);
    try{await dbWrite(file);sayStatus("Clare importada y guardada solo en este navegador.");}
    catch{sayStatus("Clare cargada; el navegador no permitió guardarla para otro inicio.");}
  }catch(error){
    URL.revokeObjectURL(url);
    sayStatus(error.message);
  }
});
// Permite arrastrar el widget sin moverlo fuera de la pantalla de Windows.
const header=$("clare-drag");
header.addEventListener("pointerdown",event=>{
  if(event.target.closest("button"))return;
  const box=dock.getBoundingClientRect();
  dragging={x:event.clientX,y:event.clientY,left:box.left,top:box.top};
  header.setPointerCapture(event.pointerId);
});
header.addEventListener("pointermove",event=>{
  if(!dragging)return;
  const maxLeft=Math.max(0,window.innerWidth-dock.offsetWidth);
  const maxTop=Math.max(0,window.innerHeight-dock.offsetHeight);
  dock.style.left=clamp(dragging.left+event.clientX-dragging.x,0,maxLeft)+"px";
  dock.style.top=clamp(dragging.top+event.clientY-dragging.y,0,maxTop)+"px";
  dock.style.right="auto";
  dock.style.bottom="auto";
});
header.addEventListener("pointerup",()=>dragging=null);
header.addEventListener("pointercancel",()=>dragging=null);
window.addEventListener("resize",()=>{
  if(!dock.style.left)return;
  dock.style.left=clamp(parseFloat(dock.style.left),0,Math.max(0,window.innerWidth-dock.offsetWidth))+"px";
  dock.style.top=clamp(parseFloat(dock.style.top),0,Math.max(0,window.innerHeight-dock.offsetHeight))+"px";
});
restoreAtlas();
