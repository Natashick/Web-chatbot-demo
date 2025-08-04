# Dockerfile
# Dies ist ein benutzerdefiniertes Dockerfile für Ihr Azure ML Environment.
# Es bietet die höchste Kontrolle über die Umgebung.

# Verwenden eines offiziellen NVIDIA CUDA-Basis-Images mit Ubuntu 22.04
FROM mcr.microsoft.com/azureml/openmpi5.0-ubuntu24.04:20250701.v1

# Optional: explizite Python-Version setzen (AzureML-Image hat meist 3.10)
# ENV PYTHON_VERSION=3.10

# Arbeitsverzeichnis setzen
WORKDIR /app

# requirements.txt kopieren und Pakete installieren
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# score.py kopieren
COPY score.py .

# (Optional) Port für FastAPI/Uvicorn freigeben, falls als Webservice genutzt
# EXPOSE 8000
