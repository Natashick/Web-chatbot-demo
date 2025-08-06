export default async function handler(req, res) {
  // CORS Headers setzen (löst das Problem!)
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  // Preflight Request
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  // Nur POST erlauben
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    // Request an Azure ML weiterleiten
    const response = await fetch('https://mein-projekt-xmise.germanywestcentral.inference.ml.azure.com/score', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer 56atAoG5g5209Q8ZaPzbHIHWYkoirMFeYD40qvggDELy31rCIvk1JQQJ99BGAAAAAAAAAAAAINFRAZML4BBd'
      },
      body: JSON.stringify(req.body)
    });
    
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
