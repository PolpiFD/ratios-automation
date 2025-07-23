# Dockerfile multi-stage pour optimiser la taille
FROM python:3.11-slim as builder

# Installer les dépendances système pour les builds
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Créer environnement virtuel
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage production
FROM python:3.11-slim

# Créer utilisateur non-root pour sécurité
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copier l'environnement virtuel
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Créer dossiers applicatifs
RUN mkdir -p /app/samples && chown -R appuser:appuser /app
WORKDIR /app

# Copier le code source
COPY --chown=appuser:appuser . .

# Passer à l'utilisateur non-root
USER appuser

# Variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Port d'exposition
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=10)"

# Commande de démarrage
CMD ["python", "-m", "app.main"] 