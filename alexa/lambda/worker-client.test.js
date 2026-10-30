"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const http = require("node:http");
const { postChat, resolveConfig, cleanHistory } = require("./worker-client");

test("rechaza JSON null sin derribar el proceso Alexa", async t => {
  const server = http.createServer((req, res) => res.end("null"));
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  t.after(() => server.close());
  await assert.rejects(postChat({ pregunta: "hola" }, {
    url: `http://127.0.0.1:${server.address().port}`,
    token: "test-token-0123456789",
    allowHttpForTests: true,
  }), { code: "worker_invalid_json" });
});

test("exige HTTPS y token largo fuera de pruebas localhost", () => {
  assert.throws(() => resolveConfig({ url: "http://example.com", token: "1234567890123456" }), { code: "worker_https_required" });
  assert.throws(() => resolveConfig({ url: "https://example.com", token: "short" }), { code: "token_missing" });
});

test("limita y valida el historial conversacional", () => {
  const history = Array.from({ length: 10 }, (_, i) => ({ role: i % 2 ? "assistant" : "user", content: "x".repeat(1300) }));
  const clean = cleanHistory(history);
  assert.equal(clean.length, 4);
  assert.equal(clean[0].content.length, 500);
});

test("envía la pregunta al contrato /chat y lee respuesta", async t => {
  const server = http.createServer((req, res) => {
    assert.equal(req.url, "/chat");
    assert.equal(req.headers.authorization, "Bearer test-token-0123456789");
    let raw = "";
    req.on("data", chunk => raw += chunk);
    req.on("end", () => {
      const body = JSON.parse(raw);
      assert.equal(body.pregunta, "hola");
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ ok: true, respuesta: "Hola desde ChatGPT" }));
    });
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  t.after(() => server.close());
  const { port } = server.address();
  const result = await postChat({ pregunta: "hola" }, {
    url: `http://127.0.0.1:${port}`,
    token: "test-token-0123456789",
    allowHttpForTests: true,
  });
  assert.equal(result.respuesta, "Hola desde ChatGPT");
});
