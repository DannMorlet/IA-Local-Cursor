import assert from "node:assert/strict";
import test from "node:test";
import {buildChatPayload} from "../matick_cloud/web/chat_payload.mjs";

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
