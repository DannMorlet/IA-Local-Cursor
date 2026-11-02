/** Construye una petición de chat sin exceder los límites públicos de Matick. */
export function buildChatPayload(history, {model = "", stateful = false,
  previousResponseId = null, conversationModel = null} = {}) {
  if (!Array.isArray(history)) throw new TypeError("Historial de chat inválido");
  const messages = [];
  let chars = 0;
  // Mantener solo turnos recientes completos; nunca enviar más de 12k caracteres.
  for (let i = history.length - 1; i >= 0 && messages.length < 12; i--) {
    const message = history[i];
    if (!message || !["user", "assistant"].includes(message.role) ||
        typeof message.content !== "string" || message.content.length < 1 ||
        message.content.length > 8000) {
      if (i === history.length - 1) throw new TypeError("Mensaje de chat inválido");
      break; // No enviar mensajes anteriores a uno que ya no cabe en el contrato.
    }
    if (chars + message.content.length > 12000) break;
    messages.unshift({role: message.role, content: message.content});
    chars += message.content.length;
  }
  if (!messages.length || messages[messages.length - 1].role !== "user") {
    throw new TypeError("Se necesita un mensaje reciente del usuario");
  }
  const request = {messages, stateful: Boolean(stateful)};
  // El modelo elegido en la interfaz debe ser el que recibe el servidor.
  if (model) request.model = model;
  if (stateful && previousResponseId && conversationModel === model) {
    request.previous_response_id = previousResponseId;
  }
  // El backend limita el cuerpo HTTP completo a 16 KiB, no a 12k caracteres.
  // UTF-8 (acentos, emojis) y el JSON pueden ocupar más bytes que el texto.
  const encoder = new TextEncoder();
  while (encoder.encode(JSON.stringify(request)).byteLength > 16 * 1024) {
    if (messages.length === 1) {
      throw new TypeError("El mensaje supera el límite HTTP de 16 KiB; acórtalo");
    }
    messages.shift(); // Descartar primero el turno más antiguo, nunca el actual.
  }
  return request;
}

/** Ignora respuestas de peticiones anteriores tras cambiar de modelo o limpiar chat. */
export function applyChatResultIfCurrent(requestEpoch, currentEpoch, apply) {
  if (requestEpoch !== currentEpoch) return false;
  apply();
  return true;
}
