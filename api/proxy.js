export default async function handler(req, res) {
  // CORS Headers setzen - Updated für Fix
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  // Preflight Request behandeln
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  // Nur POST Requests erlauben
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Only POST allowed' });
  }
  
  try {
    // Environment Variables verwenden (SICHER!)
    const azureResponse = await fetch(process.env.AZURE_ML_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.AZURE_ML_KEY}`
      },
      body: JSON.stringify(req.body)
    });
    
    if (!azureResponse.ok) {
      throw new Error(`Azure ML Error: ${azureResponse.status}`);
    }
    
    const data = await azureResponse.json();
    res.json(data);
    
  } catch (error) {
    console.error('Proxy Error:', error);
    res.status(500).json({ 
      error: 'Server error',
      message: error.message 
    });
  }
}
