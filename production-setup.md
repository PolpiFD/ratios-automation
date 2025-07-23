# 🚀 Guide de Déploiement Production

## 📋 Variables d'environnement requises

Créez un fichier `.env` sur votre serveur avec :

```bash
# Configuration de l'API
DEBUG=false
WEBHOOK_API_KEY=your-secure-api-key-here

# Azure Authentication
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-azure-tenant-id

# Azure Storage
AZURE_STORAGE_ACCOUNT_URL=https://yourstorageaccount.blob.core.windows.net
AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-storage-account-key
AZURE_BLOB_CONTAINER=file-automation-ratios

# Azure Table Storage
AZURE_STORAGE_TABLE_URL=https://yourstorageaccount.table.core.windows.net
AZURE_STORAGE_TABLE_NAME=ClientFolderIndex

# Azure Document Intelligence
AZURE_DI_ENDPOINT=https://your-di-instance.cognitiveservices.azure.com/
AZURE_DI_KEY=your-document-intelligence-key

# OneDrive
DRIVE_ID=your-onedrive-drive-id

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# LangSmith (optionnel)
LANGCHAIN_API_KEY=your-langchain-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ratios-categorisation
```

## 🛠️ Configuration serveur Infomaniak

### 1. Préparer le serveur
```bash
# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Installer Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Créer les dossiers
mkdir -p ~/ratios/data
cd ~/ratios
```

### 2. Configurer le Caddyfile
```bash
# Modifier le domaine dans Caddyfile
sed -i 's/votre-domaine.com/your-actual-domain.com/g' Caddyfile
```

### 3. Créer le volume Caddy
```bash
docker volume create caddy_data
```

## 🔐 Configuration GitHub Actions

Ajoutez ces secrets dans votre repository GitHub :

- `HOST` : IP de votre serveur Infomaniak
- `USERNAME` : nom d'utilisateur SSH
- `SSH_PRIVATE_KEY` : clé privée SSH pour la connexion

## 🚀 Premier déploiement

```bash
# Cloner le repository
git clone https://github.com/votre-username/ratios_categorisation.git ~/ratios

# Copier les fichiers de configuration
cd ~/ratios
cp docker-compose.yml docker-compose.production.yml

# Modifier l'image dans docker-compose.yml
sed -i 's/${{ github.repository }}/votre-username\/ratios_categorisation/g' docker-compose.yml

# Démarrer les services
docker compose up -d
```

## 📊 Monitoring

### Logs
```bash
# Voir les logs de l'API
docker logs ratios-api -f

# Voir les logs de Caddy
docker logs ratios-proxy -f
```

### Health check
```bash
curl https://your-domain.com/health
```

## 🔄 Mise à jour manuelle (si besoin)

```bash
cd ~/ratios
docker compose pull
docker compose up -d
docker image prune -f
``` 