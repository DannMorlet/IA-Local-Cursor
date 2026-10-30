"use strict";

/*
 * Matick Inteligente — Alexa-hosted Node.js, locale es-MX
 * Invocación candidata: «Alexa, abre Matic Set».
 *
 * Requiere ask-sdk-core (incluido en la plantilla Alexa-hosted habitual).
 * Define MATICK_BRIDGE_TOKEN como secreto/variable segura del runtime.
 * No pegues el token aquí ni lo subas a GitHub.
 *
 * Antes de reemplazar el index.js activo, guarda una copia e incorpora los
 * handlers propios que quieras conservar. Este archivo implementa las rutas
 * conocidas de esta Skill; no puede reconstruir handlers que no vimos.
 */

const Alexa = require("ask-sdk-core");
const https = require("node:https");

const WORKER_URL = process.env.MATICK_WORKER_URL
  || "https://matick-alexa-cloud.danymorlet98.workers.dev/chat";
const REQUEST_TIMEOUT_MS = 5500;
const MAX_REQUEST_BYTES = 16 * 1024;
const MAX_RESPONSE_BYTES = 16 * 1024;
const MAX_HISTORY_ITEMS = 8;
const SESSION_HISTORY_KEY = "matickHistorial";

class WorkerError extends Error {
  constructor(code) {
    super(code);
    this.name = "WorkerError";
    this.code = code;
  }
}

function cleanText(value, maxLength = 2400) {
  return String(value || "")
    .replace(/<[^>]*>/g, " ")
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, maxLength);
}

function escapeSsml(value) {
  return cleanText(value, 2600)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function safeHistory(history) {
  if (!Array.isArray(history)) return [];
  return history
    .filter(item => item
      && (item.role === "user" || item.role === "assistant")
      && typeof item.content === "string")
    .slice(-MAX_HISTORY_ITEMS)
    .map(item => ({ role: item.role, content: cleanText(item.content, 1000) }));
}

function postChat(pregunta, historial) {
  const token = process.env.MATICK_BRIDGE_TOKEN;
  if (!token || token.length < 16) {
    return Promise.reject(new WorkerError("token_missing"));
  }
  if (typeof pregunta !== "string" || !pregunta.trim()) {
    return Promise.reject(new WorkerError("question_missing"));
  }

  let url;
  try {
    url = new URL(WORKER_URL);
  } catch {
    return Promise.reject(new WorkerError("worker_url_invalid"));
  }
  if (url.protocol !== "https:") {
    return Promise.reject(new WorkerError("worker_https_required"));
  }
  url.pathname = "/chat";
  url.search = "";
  url.hash = "";

  const body = Buffer.from(JSON.stringify({
    pregunta: cleanText(pregunta, 1200),
    historial: safeHistory(historial),
  }), "utf8");
  if (body.length > MAX_REQUEST_BYTES) {
    return Promise.reject(new WorkerError("request_too_large"));
  }

  return new Promise((resolve, reject) => {
    const request = https.request(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": body.length,
        Accept: "application/json",
      },
    }, response => {
      const chunks = [];
      let byteCount = 0;

      response.on("data", chunk => {
        byteCount += chunk.length;
        if (byteCount > MAX_RESPONSE_BYTES) {
          request.destroy(new WorkerError("response_too_large"));
          return;
        }
        chunks.push(chunk);
      });

      response.on("end", () => {
        let data;
        try {
          data = JSON.parse(Buffer.concat(chunks).toString("utf8"));
        } catch {
          reject(new WorkerError("worker_invalid_json"));
          return;
        }

        if (response.statusCode < 200 || response.statusCode >= 300 || data.ok !== true) {
          const pending = String(data.error || "").toLowerCase().includes("pendiente de configuración");
          reject(new WorkerError(pending ? "worker_not_configured" : "worker_http_error"));
          return;
        }
        if (typeof data.respuesta !== "string" || !data.respuesta.trim()) {
          reject(new WorkerError("worker_answer_missing"));
          return;
        }
        resolve(data);
      });
    });

    request.setTimeout(REQUEST_TIMEOUT_MS, () => request.destroy(new WorkerError("worker_timeout")));
    request.on("error", error => {
      reject(error instanceof WorkerError ? error : new WorkerError("worker_network_error"));
    });
    request.end(body);
  });
}

function shouldSuggestWork(question, result) {
  if (result && (result.recomendar_work === true || result.suggest_work === true)) return true;
  const text = cleanText(question, 1200);
  const explicit = /\b(?:abre|abrir|inicia|iniciar|continua|continuar|pasa|pasar|manda|mandar|lleva|llevar|usa|usar|quiero seguir con|quiero usar)\b.{0,64}\b(?:codex|work)\b/i;
  const action = /\b(?:programa(?:r)?|codifica(?:r)?|revisa(?:r)?|corrige|corregir|arregla(?:r)?|depura(?:r)?|compila(?:r)?|actualiza(?:r)?|modifica(?:r)?|integra(?:r)?|ejecuta(?:r)?|construye|construir|desarrolla(?:r)?|automatiza(?:r)?)\b/i;
  const project = /\b(?:c[oó]digo|repositorio|repo|archivo(?:s)?|proyecto|aplicaci[oó]n|app|skill|worker|sistema|programa|integraci[oó]n|configuraci[oó]n|pruebas)\b/i;
  return explicit.test(text) || (action.test(text) && project.test(text));
}

function workSummary(question, answer, supplied) {
  const summary = cleanText(supplied, 1000);
  if (summary) return summary;
  return [
    "Continúa esta solicitud de Alexa en ChatGPT Work/Codex.",
    `Solicitud: ${cleanText(question, 500)}`,
    `Respuesta previa: ${cleanText(answer, 500)}`,
    "Revisa el estado del proyecto y confirma qué puedes ejecutar.",
  ].join("\n");
}

function errorMessage(error) {
  switch (error && error.code) {
    case "token_missing":
      return "La conexión segura con ChatGPT todavía no está configurada.";
    case "worker_not_configured":
      return "El servicio de ChatGPT en Cloudflare sigue pendiente de configuración.";
    case "worker_timeout":
      return "ChatGPT tardó demasiado en responder. Inténtalo de nuevo o continúa en ChatGPT Work.";
    default:
      return "No pude conectar con ChatGPT ahora. Inténtalo de nuevo en un momento.";
  }
}

function speak(handlerInput, text, endSession = false) {
  const response = handlerInput.responseBuilder.speak(escapeSsml(text));
  if (!endSession) response.reprompt("Puedes hacer otra pregunta cuando quieras.");
  return response.getResponse();
}

const LaunchRequestHandler = {
  canHandle(input) {
    return Alexa.getRequestType(input.requestEnvelope) === "LaunchRequest";
  },
  handle(input) {
    return speak(input, "Hola, soy Matick Inteligente. ChatGPT atenderá primero tus preguntas. ¿Qué quieres saber?");
  },
};

const PreguntaIntentHandler = {
  canHandle(input) {
    return Alexa.getRequestType(input.requestEnvelope) === "IntentRequest"
      && Alexa.getIntentName(input.requestEnvelope) === "PreguntaIntent";
  },
  async handle(input) {
    const pregunta = Alexa.getSlotValue(input.requestEnvelope, "consulta");
    if (!pregunta || !pregunta.trim()) {
      return speak(input, "No alcancé a escuchar la pregunta. Dímela después del tono.");
    }

    const attributes = input.attributesManager.getSessionAttributes() || {};
    const historial = safeHistory(attributes[SESSION_HISTORY_KEY]);
    try {
      const result = await postChat(pregunta, historial);
      const respuesta = cleanText(result.respuesta, 1700);
      const recommend = shouldSuggestWork(pregunta, result);
      let speech = respuesta;

      if (recommend) {
        speech += " Por el trabajo que requiere, te sugiero continuarlo en ChatGPT Work o Codex en la nube. No he abierto esas aplicaciones ni iniciado esa tarea.";
      }

      input.attributesManager.setSessionAttributes({
        ...attributes,
        [SESSION_HISTORY_KEY]: safeHistory([
          ...historial,
          { role: "user", content: pregunta },
          { role: "assistant", content: respuesta },
        ]),
      });

      const response = input.responseBuilder
        .speak(escapeSsml(speech))
        .reprompt("Puedes hacer otra pregunta cuando quieras.");

      if (recommend) {
        response.withSimpleCard(
          "Continúa en ChatGPT Work",
          "Alexa no abre Work o Codex automáticamente.\n\n"
            + workSummary(pregunta, respuesta, result.resumen_work || result.work_summary)
        );
      }
      return response.getResponse();
    } catch (error) {
      // Solo se registra un código interno; nunca la consulta, respuesta o token.
      console.error("Matick Alexa Worker error:", error && error.code ? error.code : "unexpected");
      return speak(input, errorMessage(error));
    }
  },
};

const HelpIntentHandler = {
  canHandle(input) {
    return Alexa.getRequestType(input.requestEnvelope) === "IntentRequest"
      && Alexa.getIntentName(input.requestEnvelope) === "AMAZON.HelpIntent";
  },
  handle(input) {
    return speak(input,
      "Hazme una pregunta para ChatGPT. Si requiere editar archivos o ejecutar código, te sugeriré continuar en ChatGPT Work o Codex. Alexa no puede abrir esas aplicaciones por ti.");
  },
};

const StopIntentHandler = {
  canHandle(input) {
    return Alexa.getRequestType(input.requestEnvelope) === "IntentRequest"
      && ["AMAZON.CancelIntent", "AMAZON.StopIntent"].includes(Alexa.getIntentName(input.requestEnvelope));
  },
  handle(input) {
    return speak(input, "De acuerdo. Aquí estaré cuando me necesites.", true);
  },
};

const FallbackIntentHandler = {
  canHandle(input) {
    return Alexa.getRequestType(input.requestEnvelope) === "IntentRequest"
      && Alexa.getIntentName(input.requestEnvelope) === "AMAZON.FallbackIntent";
  },
  handle(input) {
    return speak(input, "No entendí esa solicitud. Dime una pregunta para ChatGPT o pide ayuda.");
  },
};

const SessionEndedRequestHandler = {
  canHandle(input) {
    return Alexa.getRequestType(input.requestEnvelope) === "SessionEndedRequest";
  },
  handle(input) {
    return input.responseBuilder.getResponse();
  },
};

const ErrorHandler = {
  canHandle() {
    return true;
  },
  handle(input, error) {
    console.error("Matick Alexa handler error:", error && error.name ? error.name : "unexpected");
    return speak(input, "Ocurrió un problema al atender la solicitud. Inténtalo de nuevo.");
  },
};

exports.handler = Alexa.SkillBuilders.custom()
  .addRequestHandlers(
    LaunchRequestHandler,
    PreguntaIntentHandler,
    HelpIntentHandler,
    StopIntentHandler,
    FallbackIntentHandler,
    SessionEndedRequestHandler
  )
  .addErrorHandlers(ErrorHandler)
  .lambda();

