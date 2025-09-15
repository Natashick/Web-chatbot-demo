export default async function handler(req, res) {
  // CORS
  const allowOrigin = process.env.CORS_ALLOW_ORIGIN || '*';
  res.setHeader('Access-Control-Allow-Origin', allowOrigin);
  res.setHeader('Vary', 'Origin');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  // Erlaube gängige Header; erweitere bei Bedarf
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Only POST allowed' });
  }

  try {
    const endpoint =
      process.env.AZURE_ML_ENDPOINT ||
      process.env.AZURE_ML_ENDPOINT_URL; // beide Namensvarianten unterstützen
    const key =
      process.env.AZURE_ML_KEY ||
      process.env.AZURE_ML_ENDPOINT_KEY;

    if (!endpoint || !key) {
      return res.status(500).json({ error: 'Missing AZURE_ML_ENDPOINT or AZURE_ML_KEY' });
    }

    // Request-Body entpacken (beide Stile unterstützen)
    const {
      messages,
      prompt,
      context,
      parameters,
      return_json, // optional: steuert das Backend-Format, falls score.py das unterstützt
    } = req.body || {};

    // Payload vorsichtig aufbauen: nur erwartete Felder weitergeben
    const payload = {
      ...(messages ? { messages } : {}),
      ...(prompt ? { prompt } : {}),
      ...(context ? { context } : {}),
      ...(parameters ? { parameters } : {}),
      ...(typeof return_json === 'boolean' ? { return_json } : {}),
    };

    // Optionaler Timeout
    const timeoutMs = Number(process.env.PROXY_TIMEOUT_MS || 120000);
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), timeoutMs);

    const azureResp = await fetch(endpoint, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    }).catch((err) => {
      // fetch-Fehler (Netzwerk/Timeout)
      throw new Error(`Upstream fetch failed: ${err.message || String(err)}`);
    });
    clearTimeout(t);

    // Content-Type erkennen und entsprechend weitergeben
    const contentType = azureResp.headers.get('content-type') || '';
    const status = azureResp.status;

    // Antwort-Body lesen (Text immer verfügbar; JSON bei Bedarf geparst)
    const rawText = await azureResp.text();
    if (!azureResp.ok) {
      // Fehler vom Azure-Endpoint durchreichen (Body anhängen, falls vorhanden)
      res.status(status);
      // Wenn JSON-Fehler: JSON weitergeben, sonst Text
      if (contentType.includes('application/json')) {
        try {
          const errJson = JSON.parse(rawText);
          return res.json(errJson);
        } catch {
          res.setHeader('Content-Type', 'text/plain; charset=utf-8');
          return res.send(rawText || `Azure ML Error ${status}`);
        }
      } else {
        res.setHeader('Content-Type', 'text/plain; charset=utf-8');
        return res.send(rawText || `Azure ML Error ${status}`);
      }
    }

    // Erfolgsfall: JSON oder Text je nach Upstream
    if (contentType.includes('application/json')) {
      try {
        const data = JSON.parse(rawText);
        return res.status(status).json(data);
      } catch {
        // Fiel als Text zurück, obwohl Content-Type JSON – fallback als Text
        res.setHeader('Content-Type', 'text/plain; charset=utf-8');
        return res.status(status).send(rawText);
      }
    } else {
      res.setHeader('Content-Type', 'text/plain; charset=utf-8');
      return res.status(status).send(rawText);
    }
  } catch (error) {
    console.error('Proxy Error:', error);
    const msg = error?.message || String(error);
    return res.status(502).json({ error: 'Proxy error', message: msg });
  }
}
