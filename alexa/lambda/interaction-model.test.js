"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const model = require("../interactionModels/custom/es-MX.json").interactionModel.languageModel;

test("es-MX usa la frase de invocación elegida y conserva PreguntaIntent/consulta", () => {
  assert.equal(model.invocationName, "matic ia");
  const questionIntent = model.intents.find(intent => intent.name === "PreguntaIntent");
  assert.ok(questionIntent);
  assert.equal(questionIntent.slots.find(slot => slot.name === "consulta")?.type, "AMAZON.SearchQuery");
});
