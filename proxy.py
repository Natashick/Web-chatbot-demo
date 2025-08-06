from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Erlaubt CORS für alle Origins

AZURE_ENDPOINT = 'https://mein-projekt...'
AZURE_KEY = '....'

@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    resp = requests.post(
        AZURE_ENDPOINT,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {AZURE_KEY}'
        },
        json=data
    )
    return (resp.text, resp.status_code, {'Content-Type': 'application/json'})

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000)  # Erlaubt Zugriff von anderen PCs im Netzwerk
