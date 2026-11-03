import test from "node:test";
import assert from "node:assert/strict";
import {CLAIRE_ATLAS,CLAIRE_STATES,frameCoordinates,normalizeSpeechText,
        clamp,chooseSpanishVoice} from "../matick_cloud/web/clare_behavior.mjs";

test("atlas original: cuadrícula 1536 x 2288, sin desbordar filas",()=>{
  assert.equal(CLAIRE_ATLAS.width,1536);
  assert.equal(CLAIRE_ATLAS.height,2288);
  for(const state of Object.keys(CLAIRE_STATES)){
    const spec=CLAIRE_STATES[state];
    assert.ok(spec.row>=0 && spec.row<11);
    assert.ok(spec.frames>=1 && spec.frames<=8);
    const last=frameCoordinates(state,spec.frames-1,112);
    assert.ok(last.backgroundPosition.startsWith("-"));
    assert.ok(last.height.endsWith("px"));
  }
});
test("frames reinician ciclos y estados desconocidos tienen fallback",()=>{
  assert.equal(frameCoordinates("jumping",5).frame,0);
  assert.equal(frameCoordinates("inexistente",0).state,"idle");
  assert.equal(frameCoordinates("idle",-1).frame,1);
});
test("lectura elimina enlaces y no transmite scripts",()=>{
  const s=normalizeSpeechText("Hola **Clare** https://ejemplo.com <b>mundo</b>",60);
  assert.ok(s.includes("Hola Clare"));
  assert.ok(s.includes("enlace"));
  assert.ok(!s.includes("https://"));
  assert.ok(!s.includes("<b>"));
  assert.equal(normalizeSpeechText(null),"");
});
test("voz mexicana primero y española como respaldo",()=>{
  const list=[{lang:"en-US"},{lang:"es-ES"},{lang:"es-MX"}];
  assert.equal(chooseSpanishVoice(list).lang,"es-MX");
  assert.equal(chooseSpanishVoice(list.slice(0,2)).lang,"es-ES");
  assert.equal(chooseSpanishVoice([{lang:"en-US"}]),null);
});
test("movimiento nunca sale de los límites disponibles",()=>{
  assert.equal(clamp(-200,0,300),0);
  assert.equal(clamp(900,0,300),300);
  assert.equal(clamp(125,0,300),125);
});
