"use strict";
(() => {
  const $ = (selector) => document.querySelector(selector);
  const state = {
    token: sessionStorage.getItem("manguito_token") || "",
    models: [],
    connected: false,
    working: false,
    directory: ".",
    selected: "",
    proposal: null,
    messages: [],
    toastTimer: null
  };
  const pages = {
    home:"Inicio", chat:"Chat local", files:"Archivos", models:"Modelos",
    agents:"Agentes", creative:"Creatividad", devices:"Dispositivos"
  };
  const text = (selector, value) => { const element = $(selector); if (element) element.textContent = String(value); };
  const el = (tag, className, value) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = String(value);
    return node;
  };
  const join = (folder, item) => folder === "." ? item : folder + "/" + item;
  const parent = (folder) => {
    const parts = folder.split("/");
    parts.pop();
    return parts.join("/") || ".";
  };
  const showToast = (message, error = false) => {
    const node = $("#toast");
    node.textContent = String(message);
    node.classList.toggle("error", error);
    node.classList.add("visible");
    clearTimeout(state.toastTimer);
    state.toastTimer = setTimeout(() => node.classList.remove("visible"), 4500);
  };
  const setConnected = (connected) => {
    state.connected = connected;
    $("#connectionPill").classList.toggle("online", connected);
    text("#connectionLabel", connected ? "En línea" : "Sin conectar");
    text("#metricEngine", connected ? "Conectado" : "Sin conectar");
    text("#engineSub", connected ? "Manguito Gateway · localhost" : "LM Studio / OpenAI compatible");
    text("#metricWrites", "—");
    if (!connected) {
      text("#metricModels", "—");
      text("#metricWorkspace", "—");
      $("#chatModel").replaceChildren(new Option("Conectar para cargar modelos", ""));
      $("#modelList").replaceChildren(el("p", "placeholder", "Conecta tu servidor para ver modelos."));
      $("#fileList").replaceChildren(el("p", "placeholder", "Conecta Manguito para ver archivos."));
    }
  };
  async function api(path, method = "GET", data = undefined, timeout = 95000) {
    if (!state.token) throw new Error("Primero conecta Manguito con tu token local.");
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(path, {
        method,
        headers: { "Authorization": "Bearer " + state.token, ...(data === undefined ? {} : { "Content-Type": "application/json" }) },
        body: data === undefined ? undefined : JSON.stringify(data),
        cache: "no-store",
        credentials: "omit",
        signal: controller.signal
      });
      const result = await response.json();
      if (!response.ok) {
        if (response.status === 401) setConnected(false);
        throw new Error(result.error || "Error HTTP " + response.status);
      }
      return result;
    } catch (error) {
      if (error.name === "AbortError") throw new Error("Tiempo de espera agotado.");
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }
  function go(page) {
    if (!(page in pages)) return;
    for (const name of Object.keys(pages)) $("#page-" + name).classList.toggle("shown", page === name);
    for (const button of document.querySelectorAll(".nav-item")) button.classList.toggle("active", button.dataset.page === page);
    text("#currentSection", pages[page]);
    $("#app").classList.remove("menu-open");
    if (page === "files" && state.connected) loadFolder(state.directory);
    if (page === "models" && state.connected) loadModels();
    if (page === "chat") $("#chatInput").focus();
  }
  async function refresh() {
    if (!state.token) { openConnection(); return; }
    try {
      const status = await api("/v1/status", "GET", undefined, 8000);
      setConnected(true);
      text("#metricWrites", status.writes ? "Con aprobación" : "Solo lectura");
      text("#lastUpdate", "Actualizado " + new Date().toLocaleTimeString("es-MX", {hour:"2-digit",minute:"2-digit"}));
      await Promise.allSettled([loadModels(), loadWorkspaceSummary()]);
    } catch (error) {
      setConnected(false);
      showToast("No se pudo conectar: " + error.message, true);
    }
  }
  async function loadWorkspaceSummary() {
    try {
      const listing = await api("/v1/fs/list?path=.", "GET", undefined, 8000);
      text("#metricWorkspace", listing.entries.length + (listing.limited ? "+" : "") + " elementos");
    } catch (error) {
      text("#metricWorkspace", "Sin acceso");
    }
  }
  async function loadModels() {
    try {
      const data = await api("/v1/models", "GET", undefined, 12000);
      const models = Array.isArray(data.data) ? data.data.filter(x => x && typeof x.id === "string") : [];
      state.models = models;
      text("#metricModels", models.length);
      text("#modelsSub", models.length ? "Detectados en el servidor" : "Carga un modelo primero");
      const select = $("#chatModel");
      const before = select.value;
      select.replaceChildren();
      if (!models.length) select.append(new Option("Sin modelos cargados", ""));
      else for (const model of models) select.append(new Option(model.id, model.id));
      if (models.some(x => x.id === before)) select.value = before;
      const list = $("#modelList");
      list.replaceChildren();
      if (!models.length) list.append(el("p", "placeholder", "No hay modelos. Abre LM Studio y carga uno."));
      for (const model of models) {
        const card = el("div", "model-item");
        card.append(el("b", "", model.id));
        card.append(el("small", "", "Disponible vía API compatible · tipo: " + (model.object || "model")));
        list.append(card);
      }
    } catch (error) {
      state.models = [];
      text("#metricModels", "Sin servidor");
      $("#chatModel").replaceChildren(new Option("LM Studio no disponible", ""));
      $("#modelList").replaceChildren(el("p", "placeholder", "Servidor de modelos desconectado: " + error.message));
    }
  }
  function renderMessage(role, message) {
    const box = el("article", "message" + (role === "user" ? " user" : ""));
    box.append(el("div", "who", role === "user" ? "TÚ" : "MANGUITO"));
    box.append(el("div", "text", message));
    $("#messages").append(box);
    $("#messages").scrollTop = $("#messages").scrollHeight;
  }
  async function sendChat(event) {
    event.preventDefault();
    if (state.working) return;
    const input = $("#chatInput");
    const message = input.value.trim();
    const model = $("#chatModel").value;
    if (!message) return;
    if (!model) { showToast("Carga primero un modelo en LM Studio.", true); return; }
    if (!state.connected) { openConnection(); return; }
    state.working = true;
    $("#sendBtn").disabled = true;
    if ($("#messages").querySelector(".empty-chat")) $("#messages").replaceChildren();
    const history = state.messages.concat([{role:"user",content:message}]).slice(-30);
    renderMessage("user", message);
    input.value = "";
    renderMessage("assistant", "Pensando en local…");
    const thinking = $("#messages").lastElementChild;
    try {
      const answer = await api("/v1/chat", "POST", {model, messages:history});
      const reply = typeof answer.text === "string" ? answer.text : JSON.stringify(answer.text);
      thinking.querySelector(".text").textContent = reply || "(El modelo devolvió una respuesta vacía)";
      state.messages = history.concat([{role:"assistant",content:reply}]).slice(-30);
    } catch (error) {
      thinking.querySelector(".text").textContent = "Error: " + error.message;
      input.value = message;
      showToast("No se pudo completar la respuesta", true);
    } finally {
      state.working = false;
      $("#sendBtn").disabled = false;
      $("#messages").scrollTop = $("#messages").scrollHeight;
    }
  }
  function resetEditor() {
    state.selected = "";
    state.proposal = null;
    $("#fileEditor").value = "";
    $("#fileEditor").disabled = true;
    $("#previewBtn").disabled = true;
    $("#diffPreview").hidden = true;
    $("#approvalArea").hidden = true;
    $("#approvalCode").value = "";
    text("#editorFilename", "Selecciona un archivo de texto");
    text("#editorStatus", "Solo lectura inicial");
  }
  async function loadFolder(folder) {
    if (!state.connected) return;
    try {
      const listing = await api("/v1/fs/list?path=" + encodeURIComponent(folder), "GET", undefined, 8000);
      state.directory = folder;
      text("#fileLocation", folder === "." ? "/" : "/" + folder);
      const list = $("#fileList");
      list.replaceChildren();
      if (!listing.entries.length) list.append(el("p", "placeholder", "Carpeta vacía."));
      for (const item of listing.entries) {
        const filename = join(folder, item.name);
        const button = el("button", "file-entry");
        button.type = "button";
        button.append(el("span", "", item.directory ? "▣" : "▤"));
        button.append(el("b", "", item.name));
        button.addEventListener("click", () => item.directory ? loadFolder(filename) : loadFile(filename, button));
        list.append(button);
      }
      resetEditor();
    } catch (error) {
      showToast("No se pudo abrir carpeta: " + error.message, true);
    }
  }
  async function loadFile(filename, button) {
    try {
      const file = await api("/v1/fs/read?path=" + encodeURIComponent(filename), "GET", undefined, 8000);
      resetEditor();
      state.selected = filename;
      $("#fileEditor").value = file.text;
      $("#fileEditor").disabled = false;
      $("#previewBtn").disabled = false;
      text("#editorFilename", filename);
      text("#editorStatus", "Edición pendiente · no se guarda sin aprobar");
      document.querySelectorAll(".file-entry").forEach(b => b.classList.remove("selected"));
      button.classList.add("selected");
    } catch (error) {
      showToast("No se puede leer este archivo: " + error.message, true);
    }
  }
  async function previewChange() {
    if (!state.selected) return;
    state.proposal = null;
    $("#approvalArea").hidden = true;
    $("#diffPreview").hidden = true;
    try {
      const proposal = await api("/v1/fs/propose", "POST", {path:state.selected, text:$("#fileEditor").value}, 12000);
      state.proposal = proposal.proposal_id;
      $("#diffPreview").textContent = proposal.diff || "Sin cambios respecto al archivo original.";
      $("#diffPreview").hidden = false;
      if (proposal.diff) $("#approvalArea").hidden = false;
      showToast("Diff generado. El archivo no se ha modificado.");
    } catch (error) {
      showToast("No se pudo preparar el cambio: " + error.message, true);
    }
  }
  async function applyChange() {
    if (!state.proposal) return;
    const code = $("#approvalCode").value;
    if (!code) { showToast("Introduce el código de aprobación local.", true); return; }
    const confirmed = window.confirm("¿Aplicar la edición en '" + state.selected + "'? Revisa el diff primero. Se sobrescribirá el archivo dentro del workspace.");
    if (!confirmed) return;
    try {
      const result = await api("/v1/fs/apply", "POST", {proposal_id:state.proposal, approval_code:code}, 12000);
      state.proposal = null;
      $("#approvalCode").value = "";
      $("#approvalArea").hidden = true;
      $("#diffPreview").hidden = true;
      text("#editorStatus", "Guardado: " + result.path);
      showToast("Archivo actualizado correctamente.");
    } catch (error) {
      $("#approvalCode").value = "";
      showToast("No se aplicó el cambio: " + error.message, true);
    }
  }
  function openConnection() {
    $("#tokenInput").value = state.token;
    $("#backdrop").hidden = false;
    $("#tokenInput").focus();
  }
  function closeConnection() { $("#backdrop").hidden = true; }
  async function connect() {
    const candidate = $("#tokenInput").value.trim();
    if (!candidate) { showToast("Falta el token.", true); return; }
    state.token = candidate;
    sessionStorage.setItem("manguito_token", state.token);
    try {
      await api("/v1/status", "GET", undefined, 7000);
      closeConnection();
      showToast("¡Manguito conectado!");
      await refresh();
    } catch (error) {
      setConnected(false);
      showToast("Revisa el token y el servidor: " + error.message, true);
    }
  }
  function disconnect() {
    state.token = "";
    sessionStorage.removeItem("manguito_token");
    state.messages = [];
    $("#messages").replaceChildren(el("p", "placeholder", "Sesión desconectada."));
    setConnected(false);
    closeConnection();
    showToast("Sesión desconectada.");
  }
  document.querySelectorAll(".nav-item[data-page]").forEach(b => b.addEventListener("click", () => go(b.dataset.page)));
  document.querySelectorAll("[data-go]").forEach(b => b.addEventListener("click", () => go(b.dataset.go)));
  $("#menuBtn").addEventListener("click", () => $("#app").classList.toggle("menu-open"));
  $("#refreshBtn").addEventListener("click", refresh);
  $("#connectionBtn").addEventListener("click", openConnection);
  $("#connectBtn").addEventListener("click", connect);
  $("#disconnectBtn").addEventListener("click", disconnect);
  $("#tokenInput").addEventListener("keydown", e => { if (e.key === "Enter") connect(); });
  $("#chatForm").addEventListener("submit", sendChat);
  $("#newChatBtn").addEventListener("click", () => {
    if (state.working) return;
    state.messages = [];
    $("#messages").replaceChildren(el("p", "placeholder", "Nuevo chat. ¿Con qué comenzamos?"));
    $("#chatInput").focus();
  });
  $("#chatInput").addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      $("#chatForm").requestSubmit();
    }
  });
  $("#filesReload").addEventListener("click", () => loadFolder(state.directory));
  $("#modelsReload").addEventListener("click", loadModels);
  $("#goParent").addEventListener("click", () => loadFolder(parent(state.directory)));
  $("#previewBtn").addEventListener("click", previewChange);
  $("#applyBtn").addEventListener("click", applyChange);
  $("#fileEditor").addEventListener("input", () => {
    state.proposal = null;
    $("#diffPreview").hidden = true;
    $("#approvalArea").hidden = true;
  });
  $("#backdrop").addEventListener("click", e => { if (e.target === $("#backdrop")) closeConnection(); });
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") closeConnection();
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault(); go("chat");
    }
  });
  $("#themeBtn").addEventListener("click", () => {
    document.body.classList.toggle("light");
    localStorage.setItem("manguito_theme", document.body.classList.contains("light") ? "light" : "dark");
  });
  if (localStorage.getItem("manguito_theme") === "light") document.body.classList.add("light");
  if (state.token) refresh();
  else setConnected(false);
})();
