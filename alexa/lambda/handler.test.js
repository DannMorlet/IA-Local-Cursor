"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const client = require("./worker-client");
// Sustituye sólo el transporte antes de cargar el SDK; no usa credenciales ni IA real.
const original = client.postChat;
client.postChat = async ({ pregunta }) => {
  assert.match(pregunta, /red neuronal/);
  return { ok: true, respuesta: "Una red aprende patrones & relaciones." };
};
const { handler } = require("./index");
const invoke = request => new Promise((resolve, reject) => {
  handler(request, {}, (error, result) => error ? reject(error) : resolve(result));
});
client.postChat = original;

function envelope(request) {
  return {
    version: "1.0",
    session: { new: true, sessionId: "local-test", attributes: {}, user: { userId: "local-test" } },
    context: { System: { application: { applicationId: "local-test" }, user: { userId: "local-test" } } },
    request: { requestId: "local-test", locale: "es-MX", timestamp: new Date().toISOString(), ...request },
  };
}

test("LaunchRequest produce el saludo sin llamar al Worker", async () => {
  const result = await invoke(envelope({ type: "LaunchRequest" }));
  assert.match(result.response.outputSpeech.ssml, /Hola, soy Matick Inteligente/);
  assert.equal(result.response.shouldEndSession, false);
});

test("PreguntaIntent habla la respuesta simulada escapada y conserva sesión", async () => {
  const result = await invoke(envelope({ type: "IntentRequest", intent: {
    name: "PreguntaIntent", slots: { consulta: { name: "consulta", value: "qué es una red neuronal" } },
  } }));
  assert.match(result.response.outputSpeech.ssml, /patrones &amp; relaciones/);
  assert.equal(result.response.shouldEndSession, false);
  assert.equal(result.sessionAttributes.historial.length, 2);
});
