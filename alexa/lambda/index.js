"use strict";

const Alexa = require("ask-sdk-core");
const { postChat, WorkerError } = require("./worker-client");
const {
  buildWorkSuggestion,
  createWorkSummary,
  escapeSsml,
  shouldRecommendCloudWork,
} = require("./router-policy");

const MAX_HISTORY_ITEMS = 8;

function spoken(handlerInput, text, endSession = false) {
  const response = handlerInput.responseBuilder.speak(escapeSsml(text));
  if (!endSession) response.reprompt("Puedes hacer otra pregunta cuando quieras.");
  return response.getResponse();
}

function questionFrom(handlerInput) {
  const value = Alexa.getSlotValue(handlerInput.requestEnvelope, "consulta");
  return typeof value === "string" ? value.trim().slice(0, 1200) : "";
}

function historyFrom(handlerInput) {
  const attributes = handlerInput.attributesManager.getSessionAttributes() || {};
  return Array.isArray(attributes.historial) ? attributes.historial : [];
}

function errorSpeech(error) {
  if (!(error instanceof WorkerError)) {
    return "No pude completar la consulta. Inténtalo de nuevo en un momento.";
  }
  switch (error.code) {
    case "token_missing":
      return "La conexión segura con ChatGPT todavía no está configurada.";
    case "worker_not_configured":
      return "El servicio de ChatGPT en Cloudflare sigue pendiente de configuración.";
    case "worker_timeout":
      return "ChatGPT tardó más de lo que Alexa puede esperar. Vuelve a preguntarme o continúa en ChatGPT Work.";
    case "worker_https_required":
    case "worker_url_invalid":
    case "private_config_invalid":
      return "La configuración privada de la conexión con ChatGPT necesita revisión.";
    default:
      return "No pude conectar con ChatGPT ahora. Inténtalo de nuevo en un momento.";
  }
}

const LaunchRequestHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === "LaunchRequest";
  },
  handle(handlerInput) {
    return spoken(handlerInput,
      "Hola, soy Matick Inteligente. ChatGPT es mi enrutador principal. ¿Qué quieres preguntarle?");
  },
};

const QuestionIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === "IntentRequest"
      && Alexa.getIntentName(handlerInput.requestEnvelope) === "PreguntaIntent";
  },
  async handle(handlerInput) {
    const question = questionFrom(handlerInput);
    if (!question) {
      return spoken(handlerInput, "No alcancé a escuchar la pregunta. Dímela después del tono.");
    }

    const history = historyFrom(handlerInput).slice(-MAX_HISTORY_ITEMS);
    try {
      const result = await postChat({ pregunta: question, historial: history });
      const answer = result.respuesta.trim().slice(0, 2500);
      const recommendWork = shouldRecommendCloudWork(question, result);
      const speech = recommendWork
        ? answer + " " + buildWorkSuggestion(/\b(?:abre|abrir|inicia|iniciar|pasa|pasar|manda|mandar|lleva|llevar|usa|usar|quiero seguir con|quiero usar)\b.{0,64}\b(?:codex|work)\b/i.test(question))
        : answer;

      history.push({ role: "user", content: question });
      history.push({ role: "assistant", content: answer });
      handlerInput.attributesManager.setSessionAttributes({ historial: history.slice(-MAX_HISTORY_ITEMS) });

      const response = handlerInput.responseBuilder.speak(escapeSsml(speech));
      if (recommendWork) {
        const summary = createWorkSummary(question, answer, result.resumen_work || result.work_summary);
        response.withSimpleCard(
          "Continúa en ChatGPT Work",
          "Este resumen no abre ni inicia Codex automáticamente.\n\n" + summary
        );
      }
      return response.reprompt("Puedes hacer otra pregunta a ChatGPT.").getResponse();
    } catch (error) {
      // No registrar preguntas, historial, credenciales ni cuerpos del Worker.
      console.error("Matick Alexa Worker error:", error instanceof WorkerError ? error.code : "unexpected");
      return spoken(handlerInput, errorSpeech(error));
    }
  },
};

const HelpIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === "IntentRequest"
      && Alexa.getIntentName(handlerInput.requestEnvelope) === "AMAZON.HelpIntent";
  },
  handle(handlerInput) {
    return spoken(handlerInput,
      "Hazme una pregunta y ChatGPT la atenderá primero. Si la tarea requiere editar archivos o ejecutar código, te sugeriré continuar en ChatGPT Work o Codex. Alexa no puede abrir esa pantalla por ti; la app Alexa puede mostrarte un resumen.");
  },
};

const CancelAndStopIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === "IntentRequest"
      && ["AMAZON.CancelIntent", "AMAZON.StopIntent"].includes(Alexa.getIntentName(handlerInput.requestEnvelope));
  },
  handle(handlerInput) {
    return spoken(handlerInput, "De acuerdo. Aquí estaré cuando me necesites.", true);
  },
};

const FallbackIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === "IntentRequest"
      && Alexa.getIntentName(handlerInput.requestEnvelope) === "AMAZON.FallbackIntent";
  },
  handle(handlerInput) {
    return spoken(handlerInput, "No entendí esa solicitud. Dime una pregunta para ChatGPT o pide ayuda.");
  },
};

const SessionEndedRequestHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === "SessionEndedRequest";
  },
  handle(handlerInput) {
    return handlerInput.responseBuilder.getResponse();
  },
};

const ErrorHandler = {
  canHandle() {
    return true;
  },
  handle(handlerInput, error) {
    console.error("Matick Alexa handler error:", error && error.name ? error.name : "unexpected");
    return spoken(handlerInput, "Ocurrió un problema al atender la solicitud. Inténtalo de nuevo.");
  },
};

exports.handler = Alexa.SkillBuilders.custom()
  .addRequestHandlers(
    LaunchRequestHandler,
    QuestionIntentHandler,
    HelpIntentHandler,
    CancelAndStopIntentHandler,
    FallbackIntentHandler,
    SessionEndedRequestHandler
  )
  .addErrorHandlers(ErrorHandler)
  .lambda();

exports.handlers = {
  LaunchRequestHandler,
  QuestionIntentHandler,
  HelpIntentHandler,
  CancelAndStopIntentHandler,
  FallbackIntentHandler,
  SessionEndedRequestHandler,
  ErrorHandler,
};
