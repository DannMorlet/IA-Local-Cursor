"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const {
  buildWorkSuggestion,
  createWorkSummary,
  escapeSsml,
  shouldRecommendCloudWork,
} = require("./router-policy");

test("recomienda Work para pedidos explícitos aunque sean indirectos", () => {
  assert.equal(shouldRecommendCloudWork("Abre Codex para arreglar mi repositorio"), true);
  assert.equal(shouldRecommendCloudWork("quiero seguir con Work"), true);
});

test("recomienda Work para tareas técnicas de ejecución", () => {
  assert.equal(shouldRecommendCloudWork("corrige este código de mi proyecto"), true);
  assert.equal(shouldRecommendCloudWork("¿Qué significa la palabra repositorio?"), false);
});

test("limpia contenido para tarjeta y escape SSML", () => {
  assert.match(createWorkSummary("<script>repara</script>", " listo "), /Solicitud original: repara/);
  assert.equal(escapeSsml("A & B < C"), "A &amp; B &lt; C");
  assert.match(buildWorkSuggestion(true), /no puedo abrir/i);
});
