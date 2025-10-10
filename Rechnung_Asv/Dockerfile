# === Dockerfile für dein Streamlit-Projekt ===
FROM python:3.12-slim

# System-Pakete (Fonts + Locale) installieren
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        fonts-dejavu \
        fonts-liberation \
        locales && \
    rm -rf /var/lib/apt/lists/*

# deutsche Locale generieren (optional, für Formatierungen)
RUN sed -i 's/# de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
ENV LANG=de_DE.UTF-8 LC_ALL=de_DE.UTF-8

# Arbeitsverzeichnis
WORKDIR /app

# Python-Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projektdateien
COPY . .

# Streamlit-Port
EXPOSE 8501

# Startbefehl (App liegt im Root)
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
