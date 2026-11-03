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

/** Distingue un modelo configurado de un motor que haya respondido realmente. */
export function modelInventoryPresentation(inventory, settings = {}) {
  const models = Array.isArray(inventory?.models) ? inventory.models : [];
  const alternative = inventory?.provider === "openai-compatible" &&
    inventory?.configured === true;
  return {
    engineStatus: alternative ? "Proveedor compatible configurado (sin verificar)" :
      inventory?.connected ? "REST v1 disponible" : "No configurado",
    selectedModel: settings?.model ||
      (alternative && models.length === 1 ? models[0].key : ""),
  };
}

/** Ignora respuestas de peticiones anteriores tras cambiar de modelo o limpiar chat. */
export function applyChatResultIfCurrent(requestEpoch, currentEpoch, apply) {
  if (requestEpoch !== currentEpoch) return false;
  apply();
  return true;
}

/** Estado del modelo: cargado no significa que ya haya respondido por inferencia. */
export function modelReadiness({token="", inventoryFresh=false, selected="",
    provider="", models=[]}={}) {
  if(!token) return {ok:false, reason:"Conecta tu servidor Matick antes de enviar."};
  if(!inventoryFresh) return {ok:false, reason:"Actualiza el catálogo de modelos para comprobar su disponibilidad."};
  if(!selected) return {ok:false, reason:"Selecciona un modelo en Modelos IA."};
  const item=Array.isArray(models) ? models.find(m=>m?.key===selected) : null;
  if(!item) return {ok:false, reason:"El modelo elegido ya no aparece en el catálogo. Actualiza Modelos IA."};
  if(provider==="rest-v1" && (!Array.isArray(item.loaded_instances) || !item.loaded_instances.length))
    return {ok:false, reason:"Modelo elegido pero NO cargado en RAM/VRAM. En Modelos IA pulsa Cargar."};
  return {ok:true, verifiedInference:false};
}

/** La aceptación de /models/load no demuestra que el modelo esté en memoria. */
export function modelLoadFeedback({provider="", inventoryFresh=false, models=[]}={}, model="") {
  if(!inventoryFresh) return "Carga solicitada, pero no se pudo comprobar el estado del motor.";
  const item=Array.isArray(models) ? models.find(row=>row?.key===model) : null;
  if(!item) return "Carga solicitada; el modelo no aparece en el catálogo actualizado.";
  if(provider!=="rest-v1")
    return "Solicitud enviada al proveedor; inferencia todavía sin verificar.";
  return Array.isArray(item.loaded_instances) && item.loaded_instances.length ?
    "Instancia declarada cargada por REST v1; inferencia aún sin verificar." :
    "Carga solicitada; REST v1 todavía no confirma una instancia cargada.";
}


/** Evita que respuestas tardías del catálogo sustituyan un inventario más nuevo. */
export function inventoryRequestIsCurrent(requestId, activeId, requestToken, activeToken) {
  return requestId === activeId && Boolean(requestToken) && requestToken === activeToken;
}


/** Solo la autenticación más reciente y no cancelada puede activar una sesión. */
export function loginAttemptIsCurrent(requestId, activeId, requestToken, enteredToken) {
  return requestId === activeId && Boolean(requestToken) && requestToken === enteredToken;
}

/** Al autenticar una sesión nueva, nunca heredar estado de otra cuenta/token. */
export function resetForAuthenticatedSession(state) {
  state.chatEpoch++;
  state.inventoryRequestId++;
  state.taskRequestId++;
  state.chat=[];
  state.previousResponseId=null;
  state.conversationModel=null;
  state.models=[];
  state.provider="";
  state.inventoryFresh=false;
  state.selected="";
  state.loadedInstances=[];
  state.tasks=[];
}

/** La aceptación de /models/unload tampoco prueba liberación de VRAM física. */
export function modelUnloadFeedback({provider="", inventoryFresh=false, models=[]}={}, model="", instanceId="") {
  if(!inventoryFresh) return "Descarga solicitada, pero no se pudo verificar el inventario.";
  const item=Array.isArray(models) ? models.find(row=>row?.key===model) : null;
  if(!item) return "Descarga solicitada; el modelo ya no aparece en el catálogo.";
  if(provider!=="rest-v1") return "Solicitud enviada; el proveedor no confirma la memoria liberada.";
  const instances=Array.isArray(item.loaded_instances) ? item.loaded_instances : [];
  return instances.some(row=>row?.id===instanceId) ?
    "Descarga solicitada; REST v1 todavía reporta la instancia cargada." :
    "REST v1 ya no reporta la instancia; RAM/VRAM física sin medir.";
}

/** Serializa acciones de modelos para impedir cargas/descargas duplicadas por doble clic. */
export function createExclusiveAction(onBusyChange=()=>{}) {
  let busy=false;
  return async operation=>{
    if(busy) return false;
    busy=true;
    try {
      onBusyChange(true);
      await operation();
      return true;
    } finally {
      busy=false;
      onBusyChange(false);
    }
  };
}
