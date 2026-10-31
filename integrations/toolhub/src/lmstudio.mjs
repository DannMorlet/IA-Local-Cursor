// SDK de LM Studio como proveedor opcional, NO reemplaza el motor propio de Matick.
export function normalizeSdkUrl(input = 'ws://127.0.0.1:1234') {
  const url = new URL(input);
  if (!['ws:', 'wss:'].includes(url.protocol) || url.username || url.password
    || url.search || url.hash || url.pathname !== '/') {
    throw new Error('MATICK_LMSTUDIO_WS debe ser ws://host:puerto o wss://host:puerto, sin credenciales ni rutas');
  }
  if (url.protocol === 'ws:' && !['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname)) {
    throw new Error('LM Studio remoto requiere wss://; para LAN configura un túnel TLS autenticado');
  }
  return url.origin;
}

export async function createLmStudioAdapter({
  baseUrl = process.env.MATICK_LMSTUDIO_WS || 'ws://127.0.0.1:1234',
  ClientClass,
} = {}) {
  const safeUrl = normalizeSdkUrl(baseUrl);
  // Carga dinámica: cloud y MatickStudioLM.exe siguen funcionando sin LM Studio instalado.
  const LMStudioClient = ClientClass || (await import('@lmstudio/sdk')).LMStudioClient;
  const client = new LMStudioClient({ baseUrl: safeUrl });
  return {
    provider: 'lmstudio-js',
    endpoint: safeUrl,
    async listModels() {
      const models = await client.llm.listLoaded();
      return models.map(model => ({
        identifier: String(model.identifier ?? model.modelKey ?? 'modelo-cargado'),
        path: model.path ? String(model.path) : null,
      }));
    },
    async respond(prompt, modelId) {
      if (typeof prompt !== 'string' || !prompt.trim() || prompt.length > 12000) {
        throw new Error('El prompt debe ser texto de 1 a 12000 caracteres');
      }
      const model = modelId
        ? await client.llm.model(modelId)
        : await client.llm.model();
      const answer = await model.respond(prompt);
      return { provider: 'lmstudio-js', content: answer.content };
    },
  };
}
