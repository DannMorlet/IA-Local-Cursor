/** Mini-Clare: lógica de animación sin dependencias, apta para tests Node. */
export const CLAIRE_ATLAS={width:1536,height:2288,columns:8,rows:11,frameWidth:192,frameHeight:208};
export const CLAIRE_STATES=Object.freeze({
  idle:{row:0,frames:6},
  "running-right":{row:1,frames:8},
  "running-left":{row:2,frames:8},
  waving:{row:3,frames:4},
  jumping:{row:4,frames:5},
  failed:{row:5,frames:8},
  waiting:{row:6,frames:6},
  running:{row:7,frames:6},
  review:{row:8,frames:6},
});
export function frameCoordinates(state="idle",step=0,displayWidth=112){
  const s=CLAIRE_STATES[state]||CLAIRE_STATES.idle;
  const n=Number.isFinite(step)?Math.abs(Math.trunc(step)):0;
  const frame=n%s.frames;
  const size=Math.max(24,Math.min(192,Number(displayWidth)||112));
  const ratio=size/CLAIRE_ATLAS.frameWidth;
  return {
    state:CLAIRE_STATES[state]?state:"idle",
    frame,
    backgroundSize:(CLAIRE_ATLAS.width*ratio)+"px "+(CLAIRE_ATLAS.height*ratio)+"px",
    backgroundPosition:(-frame*size)+"px "+(-s.row*CLAIRE_ATLAS.frameHeight*ratio)+"px",
    width:size+"px",
    height:(CLAIRE_ATLAS.frameHeight*ratio)+"px"
  };
}
export function normalizeSpeechText(input,maxLength=500){
  if(typeof input!=="string") return "";
  const clean=input
    .replace(/\[([^\]]+)\]\([^)]*\)/g,"$1")
    .replace(/https?:\/\/\S+/gi,"enlace")
    .replace(/[`*_#<>]/g,"")
    .replace(/\s+/g," ").trim();
  return clean.slice(0,Math.max(1,Math.min(2000,maxLength)));
}
export function clamp(value,lo,hi){
  const x=Number.isFinite(value)?value:lo;
  return Math.min(Math.max(x,lo),Math.max(lo,hi));
}
export function chooseSpanishVoice(voices){
  if(!Array.isArray(voices)) return null;
  return voices.find(v=>/^es[-_]mx$/i.test(v.lang))||
         voices.find(v=>/^es[-_]/i.test(v.lang))||null;
}
