export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Only POST allowed' });
  }

  try {
    // Sicherstellen, dass body immer korrekt ist
    let body = req.body;
    if (!body || typeof body !== 'object') {
      try { body = JSON.parse(req.body); } catch (e) { body = {}; }
    }

    const endpoint = process.env.AZURE_ML_ENDPOINT;
    const key = process.env.AZURE_ML_KEY;
    if (!endpoint || !key) {
      throw new Error('Azure Endpoint/Key nicht gesetzt!');
    }

    const azureResponse = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${key}`
      },
      body: JSON.stringify(body)
    });

    const data = await azureResponse.json();
    if (!azureResponse.ok) {
      throw new Error(`Azure ML Error: ${azureResponse.status} - ${JSON.stringify(data)}`);
    }

    res.json(data);

  } catch (error) {
    // CORS auch bei Fehlern!
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    console.error('Proxy Error:', error);
    res.status(500).json({ 
      error: 'Server error',
      message: error.message 
    });
  }
}
