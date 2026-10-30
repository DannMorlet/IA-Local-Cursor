"use strict";

const EXPLICIT_WORK_REQUEST = /\b(?:abre|abrir|inicia|iniciar|continua|continuar|pasa|pasar|manda|mandar|lleva|llevar|usa|usar|quiero seguir con|quiero usar)\b.{0,64}\b(?:codex|work)\b/i;
const EXECUTION_ACTION = /\b(?:programa(?:r)?|codifica(?:r)?|revisa(?:r)?|corrige|corregir|arregla(?:r)?|depura(?:r)?|compila(?:r)?|actualiza(?:r)?|modifica(?:r)?|integra(?:r)?|ejecuta(?:r)?|construye|construir|desarrolla(?:r)?|automatiza(?:r)?|continua(?:r)?)\b/i;
const PROJECT_OBJECT = /\b(?:c[oó]digo|repositorio|\brepo\b|archivo(?:s)?|proyecto|aplicaci[oó]n|\bapp\b|skill|worker|sistema|programa|integraci[oó]n|configuraci[oó]n|pruebas|compilaci[oó]n)\b/i;

function cleanText(value, limit = 2500) {
  return String(value || "")
    .replace(/<[^>]*>/g, " ")
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, limit);
}

function shouldRecommendCloudWork(question, workerResult = {}) {
  if (workerResult.recomendar_work === true || workerResult.suggest_work === true) return true;
  const query = cleanText(question, 1500);
  if (EXPLICIT_WORK_REQUEST.test(query)) return true;
  return EXECUTION_ACTION.test(query) && PROJECT_OBJECT.test(query);
}

function createWorkSummary(question, answer, workerSummary) {
  const provided = cleanText(workerSummary, 1200);
  if (provided) return provided;
  const request = cleanText(question, 700);
  const reply = cleanText(answer, 700);
  return [
    "Continúa esta solicitud de Alexa en ChatGPT Work/Codex.",
    "Solicitud original: " + request,
    reply ? "Respuesta previa de ChatGPT: " + reply : "",
    "Primero revisa el estado actual del proyecto y confirma qué puedes ejecutar.",
  ].filter(Boolean).join("\n");
}

function escapeSsml(value) {
  return cleanText(value, 3000)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function formatQuestionForVoice(question) {
  const text = cleanText(question, 1200);
  if (/\b(detallad[oa]|a detalle|paso a paso|explica(?:me)? con profundidad|c[oó]digo completo)\b/i.test(text)) {
    return text;
  }
  return [
    "Responde en español de México, pensado para escucharse en voz alta.",
    "Da primero la respuesta principal, en no más de dos frases breves y unas 35 palabras.",
    "No incluyas bloques de código. Si requiere modificar archivos o ejecutar código, resume el siguiente paso y sugiere ChatGPT Work o Codex.",
    "Pregunta: " + text,
  ].join(" ");
}

function buildWorkSuggestion(explicit) {
  if (explicit) {
    return "No puedo abrir Codex o Work desde el Echo. Para ejecutar esta tarea en la nube, te sugiero continuar en ChatGPT Work o Codex; dejé un resumen en la tarjeta de la app Alexa.";
  }
  return "Por el trabajo que requiere, te sugiero continuarlo en ChatGPT Work o Codex en la nube. No he iniciado esa ejecución; dejé un resumen en la tarjeta de la app Alexa.";
}

module.exports = {
  buildWorkSuggestion,
  createWorkSummary,
  escapeSsml,
  formatQuestionForVoice,
  shouldRecommendCloudWork,
};
