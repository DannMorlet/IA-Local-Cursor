"use strict";

const http = require("node:http");
const https = require("node:https");

const DEFAULT_WORKER_URL = "https://matick-alexa-cloud.danymorlet98.workers.dev";
const MAX_REQUEST_BYTES = 16 * 1024;
const MAX_RESPONSE_BYTES = 16 * 1024;
const REQUEST_TIMEOUT_MS = 5200;

class WorkerError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "WorkerError";
    this.code = code;
  }
}

function privateConfig() {
  try {
    return require("./config.private.json");
  } catch (error) {
    if (error && error.code === "MODULE_NOT_FOUND") return {};
    throw new WorkerError("private_config_invalid", "La configuración privada no se pudo leer.");
  }
}

function resolveConfig(override) {
  const file = privateConfig();
  const config = override || {};
  const baseUrl = config.url || process.env.MATICK_WORKER_URL || file.workerUrl || DEFAULT_WORKER_URL;
  const token = config.token || process.env.MATICK_BRIDGE_TOKEN || file.bridgeToken || file.token || "";
  let url;
  try {
    url = new URL(baseUrl);
  } catch {
    throw new WorkerError("worker_url_invalid", "La dirección del Worker no es válida.");
  }
  if (url.protocol !== "https:" && !(config.allowHttpForTests === true && url.hostname === "127.0.0.1")) {
    throw new WorkerError("worker_https_required", "El Worker debe usar HTTPS.");
  }
  if (!token || token.length < 16) {
    throw new WorkerError("token_missing", "Falta el token privado de conexión con Cloudflare.");
  }
  url.pathname = "/chat";
  url.search = "";
  url.hash = "";
  return { url, token, timeoutMs: config.timeoutMs || REQUEST_TIMEOUT_MS };
}

function cleanHistory(history) {
  if (!Array.isArray(history)) return [];
  return history
    .filter(item => item && (item.role === "user" || item.role === "assistant") && typeof item.content === "string")
    .slice(-4)
    .map(item => ({ role: item.role, content: item.content.slice(0, 500) }));
}

function postChat({ pregunta, historial = [] }, overrideConfig) {
  if (typeof pregunta !== "string" || !pregunta.trim()) {
    return Promise.reject(new WorkerError("question_missing", "No recibí la pregunta de voz."));
  }
  const question = pregunta.trim().slice(0, 1200);
  const history = cleanHistory(historial);
  const body = Buffer.from(JSON.stringify({ pregunta: question, historial: history }), "utf8");
  if (body.length > MAX_REQUEST_BYTES) {
    return Promise.reject(new WorkerError("request_too_large", "La solicitud excede el tamaño permitido."));
  }

  let config;
  try {
    config = resolveConfig(overrideConfig);
  } catch (error) {
    return Promise.reject(error);
  }
  const transport = config.url.protocol === "https:" ? https : http;

  return new Promise((resolve, reject) => {
    const request = transport.request(config.url, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + config.token,
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": body.length,
        Accept: "application/json",
      },
    }, response => {
      const chunks = [];
      let size = 0;
      response.on("data", chunk => {
        size += chunk.length;
        if (size > MAX_RESPONSE_BYTES) {
          request.destroy(new WorkerError("response_too_large", "La respuesta excede el tamaño permitido."));
          return;
        }
        chunks.push(chunk);
      });
      response.on("end", () => {
        let data;
        try {
          data = JSON.parse(Buffer.concat(chunks).toString("utf8"));
        } catch {
          reject(new WorkerError("worker_invalid_json", "El Worker devolvió una respuesta inválida."));
          return;
        }
        if (!data || typeof data !== "object" || Array.isArray(data)) {
          reject(new WorkerError("worker_invalid_json", "El Worker devolvió una estructura inválida."));
          return;
        }
        if (response.statusCode < 200 || response.statusCode >= 300 || data.ok !== true) {
          const pending = String(data.error || "").toLowerCase().includes("pendiente de configuración");
          reject(new WorkerError(
            pending ? "worker_not_configured" : "worker_http_error",
            pending ? "El Worker de ChatGPT todavía está pendiente de configuración." : "El Worker rechazó la solicitud."
          ));
          return;
        }
        if (typeof data.respuesta !== "string" || !data.respuesta.trim()) {
          reject(new WorkerError("worker_answer_missing", "El Worker no devolvió una respuesta hablable."));
          return;
        }
        resolve(data);
      });
    });

    request.setTimeout(config.timeoutMs, () => {
      request.destroy(new WorkerError("worker_timeout", "La respuesta tardó más de lo permitido para Alexa."));
    });
    request.on("error", error => {
      if (error instanceof WorkerError) reject(error);
      else reject(new WorkerError("worker_network_error", "No se pudo conectar con el Worker."));
    });
    request.end(body);
  });
}

module.exports = { DEFAULT_WORKER_URL, WorkerError, cleanHistory, postChat, resolveConfig };
