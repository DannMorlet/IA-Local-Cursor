import assert from "node:assert/strict";
import test from "node:test";
import {buildChatPayload, applyChatResultIfCurrent, modelInventoryPresentation, modelReadiness, modelLoadFeedback} from "../matick_cloud/web/chat_payload.mjs";

test("el proveedor alternativo aparece sin fingir inferencia verificada", () => {
  const inventory = {provider: "openai-compatible", configured: true, connected: false,
    models: [{key: "modelo-alternativo", source: "openai-compatible"}]};
  assert.deepEqual(modelInventoryPresentation(inventory, {model: null}), {
    engineStatus: "Proveedor compatible configurado (sin verificar)",
    selectedModel: "modelo-alternativo",
  });
  assert.equal(modelInventoryPresentation(inventory, {model: "modelo-guardado"}).selectedModel,
               "modelo-guardado");
  assert.deepEqual(modelInventoryPresentation({models: [], connected: false}, {}), {
    engineStatus: "No configurado", selectedModel: "",
  });
  assert.equal(modelInventoryPresentation({connected: true, models: []}, {}).engineStatus,
               "REST v1 disponible");
});

const user = text => ({role: "user", content: text});
const assistant = text => ({role: "assistant", content: text});

test("el modelo seleccionado en la interfaz se envía a /v1/chat", () => {
  const request = buildChatPayload([user("hola")], {model: "modelo-b"});
  assert.deepEqual(request, {messages: [user("hola")], stateful: false, model: "modelo-b"});
});

test("la sesión stateful solo continúa si el modelo coincide", () => {
  const history = [user("hola"), assistant("qué tal"), user("continúa")];
  const request = buildChatPayload(history, {model: "modelo-b", stateful: true,
    previousResponseId: "resp_abc", conversationModel: "modelo-a"});
  assert.equal(request.previous_response_id, undefined);
  const resumed = buildChatPayload(history, {model: "modelo-b", stateful: true,
    previousResponseId: "resp_abc", conversationModel: "modelo-b"});
  assert.equal(resumed.previous_response_id, "resp_abc");
});

test("los chats largos mantienen turnos recientes completos dentro de límites", () => {
  const history = [user("a".repeat(6500)), assistant("b".repeat(6500)), user("c".repeat(6500))];
  const request = buildChatPayload(history, {model: "modelo-b"});
  assert.deepEqual(request.messages, [user("c".repeat(6500))]);
  assert.ok(request.messages.reduce((n, message) => n + message.content.length, 0) <= 12000);
  const short = Array.from({length: 30}, (_, i) => i % 2 ? assistant("bien") : user("hola"));
  short.push(user("última pregunta"));
  assert.equal(buildChatPayload(short).messages.length, 12);
  assert.deepEqual(buildChatPayload([assistant("x".repeat(9000)), user("pregunta nueva")]).messages,
                   [user("pregunta nueva")]);
});

test("los historiales inválidos no producen peticiones rotas", () => {
  assert.throws(() => buildChatPayload([]), TypeError);
  assert.throws(() => buildChatPayload([assistant("hola")]), TypeError);
  assert.throws(() => buildChatPayload([user("x".repeat(8001))]), TypeError);
});


test("el cuerpo HTTP del chat respeta 16 KiB reales con UTF-8 y JSON", () => {
  // El servidor limita Content-Length, no la cantidad de caracteres JavaScript.
  const history = [user("hola"), assistant("漢".repeat(5000)), user("🥭".repeat(3000))];
  const request = buildChatPayload(history, {model: "modelo-ñ"});
  assert.deepEqual(request.messages, [user("🥭".repeat(3000))]);
  assert.ok(new TextEncoder().encode(JSON.stringify(request)).byteLength <= 16 * 1024);
  // Los mensajes cortos con acentos no deben descartarse.
  const short = buildChatPayload([user("¡Qué tal! 🥭"), assistant("Bien"), user("continúa")]);
  assert.equal(short.messages.length, 3);
});

test("rechaza el último mensaje si ni solo cabe en el límite HTTP", () => {
  // 6k caracteres válidos por mensaje, pero 18k bytes antes del JSON.
  assert.throws(() => buildChatPayload([user("漢".repeat(6000))]), /16 KiB/);
  // El nombre de modelo también forma parte del tamaño real de la petición.
  assert.throws(() => buildChatPayload([user("hola")], {model: "漢".repeat(6000)}), /16 KiB/);
});

test("respuestas tardías no contaminan otro modelo ni un chat limpiado", async () => {
  let epoch = 3;
  const sentEpoch = epoch;
  let complete;
  const pending = new Promise(resolve => { complete = resolve; });
  const messages = [];
  // Cambiar de modelo mientras la solicitud está pendiente invalida la respuesta.
  epoch++;
  complete({content: "respuesta del modelo anterior"});
  const response = await pending;
  assert.equal(applyChatResultIfCurrent(sentEpoch, epoch,
    () => messages.push(response.content)), false);
  assert.deepEqual(messages, []);
  // Volver al modelo original no revalida una respuesta antigua.
  epoch++;
  assert.equal(applyChatResultIfCurrent(sentEpoch, epoch,
    () => messages.push(response.content)), false);
  // Las respuestas actuales sí se muestran.
  const currentEpoch = epoch;
  assert.equal(applyChatResultIfCurrent(currentEpoch, epoch,
    () => messages.push("respuesta actual")), true);
  assert.deepEqual(messages, ["respuesta actual"]);
  // Limpiar la conversación también descarta errores pendientes.
  epoch++;
  assert.equal(applyChatResultIfCurrent(currentEpoch, epoch,
    () => messages.push("error tardío")), false);
});


test("el chat exige autenticación, inventario vigente y modelo disponible", () => {
  const ready = {token:"token-local", inventoryFresh:true, selected:"modelo-a",
    provider:"rest-v1", models:[{key:"modelo-a", loaded_instances:[{id:"instancia-a"}]}]};
  assert.match(modelReadiness({...ready, token:""}).reason, /Conecta/);
  assert.match(modelReadiness({...ready, inventoryFresh:false}).reason, /Actualiza/);
  assert.match(modelReadiness({...ready, selected:""}).reason, /Selecciona/);
  assert.match(modelReadiness({...ready, selected:"modelo-b"}).reason, /ya no aparece/);
  assert.match(modelReadiness({...ready, models:[]}).reason, /ya no aparece/);
});

test("REST v1 no permite chatear con modelo solo seleccionado pero sin cargar", () => {
  const ready = {token:"token-local", inventoryFresh:true, selected:"modelo-a",
    provider:"rest-v1", models:[{key:"modelo-a", loaded_instances:[]}]};
  assert.equal(modelReadiness(ready).ok, false);
  assert.match(modelReadiness(ready).reason, /NO cargado/);
  assert.deepEqual(modelReadiness({...ready,
    models:[{key:"modelo-a", loaded_instances:[{id:"instancia-a"}]}]}),
    {ok:true, verifiedInference:false});
});

test("proveedor compatible no presume inferencia verificada sin pesos reales", () => {
  const state = {token:"token-local", inventoryFresh:true, selected:"modelo-a",
    provider:"openai-compatible", models:[{key:"modelo-a", source:"openai-compatible"}]};
  assert.deepEqual(modelReadiness(state), {ok:true, verifiedInference:false});
});

test("cargar no significa inferir: confirma solo la instancia reportada por REST v1", () => {
  const state={provider:"rest-v1", inventoryFresh:true,
    models:[{key:"modelo-a",loaded_instances:[]}]};
  assert.match(modelLoadFeedback(state,"modelo-a"), /todavía no confirma/);
  assert.match(modelLoadFeedback({...state,models:[{key:"modelo-a",
    loaded_instances:[{id:"instancia-1"}]}]},"modelo-a"), /declarada cargada/);
  assert.match(modelLoadFeedback({...state,inventoryFresh:false},"modelo-a"),
    /no se pudo comprobar/);
  assert.match(modelLoadFeedback(state,"modelo-inexistente"), /no aparece/);
  assert.match(modelLoadFeedback({...state,provider:"openai-compatible"},"modelo-a"),
    /inferencia todavía sin verificar/);
});
