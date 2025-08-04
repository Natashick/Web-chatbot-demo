# Cybersecurity Web-Chatbot mit Mistral-7B auf Azure

Ein intelligenter Chatbot für Cybersecurity-Dokumentation, basierend auf einem feinjustierten Mistral-7B-Modell und deployt auf Microsoft Azure.

## Projektübersicht

Dieses Projekt entwickelt einen KI-basierten Web-Chatbot zur effizienten Dokumentationsrecherche und schnellen Einarbeitung neuer Mitarbeiter. Der Bot nutzt ein auf Cybersecurity-Standards spezialisiertes Mistral-7B-Modell und ist vollständig in der Azure-Cloud deployt.


##  Technologie-Stack

### **Frontend**
- **HTML5/CSS3** - Responsive Web-Interface
- **JavaScript (ES6+)** - Asynchrone API-Kommunikation
- **GitHub Pages** - Kostenfreies Web-Hosting

### **Backend & KI**
- **Microsoft Azure ML** - Cloud-ML-Plattform
- **Mistral-7B-v0.1** - Base Large Language Model
- **PEFT (Parameter-Efficient Fine-Tuning)** - Effizientes Training
- **QLoRA** - 4-bit Quantisierung für Speicheroptimierung
- **BitsAndBytes** - Quantisierungsbibliothek

### **Entwicklung & Deployment**
- **Python 3.10+** - Hauptprogrammiersprache
- **Azure CLI** - Cloud-Deployment und -Management
- **Docker** - Containerisierung
- **Git/GitHub** - Versionskontrolle

##  Projektstruktur

cyber-bot-func/
├──  webchat.html              # Frontend Web-Interface
├──  score_backup_fixed.py     # Optimiertes ML-Inferenz-Script
├──  proxy.py                  # Lokaler CORS-Proxy (optional)
├──  requirements.txt          # Python-Dependencies
├──  Dockerfile                # Container-Definition
├──  deployment.yaml           # Azure ML Deployment-Config
├──  endpoint.yaml             # Azure ML Endpoint-Config
├──  doku/                     # Projektdokumentation
│   ├── Projektantrag_Chatbot_Mistral7B.doc
│   └── regeln.txt
├──  README.md                 # Diese Datei
└──  README_*.md               # Detaillierte Deployment-Guides

##  Installation & Setup

### **Voraussetzungen**
- Python 3.10+
- Azure CLI installiert und konfiguriert
- Azure-Subscription mit ML-Workspace
- Git

### **1. Repository klonen**
```bash
git clone https://github.com/username/cyber-bot-func.git
cd cyber-bot-func
```

### **2. Python-Umgebung einrichten**
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

### **3. Azure ML Model deployen**
```bash
# Azure anmelden
az login

# ML-Workspace setzen
az configure --defaults workspace=<your-workspace> group=<your-resource-group>

# Endpoint erstellen
az ml online-endpoint create -f endpoint.yaml

# Model deployen
az ml online-deployment create -f deployment.yaml

# Traffic aktivieren
az ml online-endpoint update -n mein-projekt-xmise --traffic mistral-7b-finetuned-peft-reg-1=100
```

### **4. Frontend konfigurieren**
1. **Endpoint-URL abrufen:**
   ```bash
   az ml online-endpoint show -n mein-projekt-xmise --query scoring_uri
   ```

2. **API-Key abrufen:**
   ```bash
   az ml online-endpoint get-credentials -n mein-projekt-xmise
   ```

3. **webchat.html aktualisieren:**
   ```javascript
   const AZURE_ENDPOINT = 'https://your-endpoint.inference.ml.azure.com/score';
   const AZURE_KEY = 'your-api-key';
   ```

##  Verwendung

### **Lokaler Test**
```bash
# Frontend starten
python -m http.server 8080

# Browser öffnen
open http://localhost:8080/webchat.html
```

### **Öffentlicher Zugriff**
1. Repository auf GitHub hochladen
2. GitHub Pages aktivieren (Settings → Pages)
3. Zugriff über: `https://username.github.io/repo-name/webchat.html`


##  Konfiguration

### **Model-Parameter (score_backup_fixed.py)**
```python
# Token-Limits basierend auf Fragetyp
max_tokens = {
    'simple_questions': 100-150,
    'complex_questions': 250-500,
    'detailed_explanations': 400-700
}

# Sampling-Parameter
temperature = 0.3      # Konservativ für Genauigkeit
top_k = 20            # Begrenzte Wortauswahl
top_p = 0.7           # Fokussierte Generierung
```

### **Performance-Optimierung**
- **Intelligente Token-Anpassung** basierend auf Fragetyp
- **Wiederholungserkennung** und automatisches Stoppen
- **Halluzinations-Validierung** für korrekte Antworten

##  Fehlerbehebung

### **Häufige Probleme**

**1. CORS-Fehler beim direkten Endpoint-Zugriff**
```bash
# Lösung: Lokalen Proxy verwenden
python proxy.py
# Frontend auf http://localhost:5000/api/ask umstellen
```

**2. Timeout-Fehler**
```yaml
# deployment.yaml erweitern
request_settings:
  request_timeout_ms: 180000  # 3 Minuten
```

**3. Model generiert Wiederholungen**
```python
# Parameter anpassen
repetition_penalty = 1.2
temperature = 0.3  # Weniger kreativ
```

Detaillierte Troubleshooting-Guides: siehe `README3_AZURE_FEHLER_UND_LOESUNGEN.md`

##  Performance-Metriken

- **Antwortzeit:** 6-15 Sekunden (optimiert)
- **Genauigkeit:** Basiert auf Fine-Tuning-Daten
- **Verfügbarkeit:** 99.9% (Azure SLA)
- **Skalierung:** Automatisch durch Azure ML

##  Sicherheit

- **API-Key-Authentifizierung** für Azure ML Endpoint
- **HTTPS-Verschlüsselung** für alle API-Calls
- **Rate-Limiting** durch Azure ML
- **Keine Speicherung** von Chat-Daten

##  Kostenübersicht

### **Azure ML Online Endpoint**
- **Compute:** Standard_NC4as_T4_v3 (~$1-3/Stunde bei Nutzung)
- **Storage:** Vernachlässigbar für Model-Hosting
- **Requests:** $0.50 pro 1000 Inferenz-Calls

### **Kostenoptimierung**
- **Auto-Scaling:** Endpoint läuft nur bei Anfragen
- **Shared Compute:** Mehrere Deployments pro Endpoint möglich
- **Monitoring:** Azure Cost Management für Kostenkontrolle

##  Nächste Schritte

### **Kurzfristig**
- [ ] CORS-Probleme vollständig lösen
- [ ] Performance-Monitoring implementieren
- [ ] User-Feedback-System hinzufügen

### **Mittelfristig**
- [ ] RAG (Retrieval-Augmented Generation) für bessere Genauigkeit
- [ ] Multi-Document-Support erweitern
- [ ] Chat-History implementieren

### **Langfristig**
- [ ] Voice-Interface hinzufügen
- [ ] Integration in Unternehmens-Systeme
- [ ] Multi-Language-Support

## 👥 Entwicklung

Dieses Repository enthält einen vollständigen AI-Chatbot mit modernen Cloud-Technologien.

##  Lizenz

MIT License - Frei für persönliche und kommerzielle Nutzung.

##  Weitere Dokumentation

- [Detailliertes Azure-Deployment](README2_AZURE_DEPLOY_DETAIL.md)
- [Fehlerbehandlung & Troubleshooting](README3_AZURE_FEHLER_UND_LOESUNGEN.md)
- [Projekt-Dokumentation](doku/)

---

** Ein modernes Beispiel für den Einsatz von Large Language Models in der Praxis!**