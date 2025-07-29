# 🚀 Guide de Déploiement VPS - Ratios Categorisation

## 📋 Vue d'ensemble

**Principe** : Push sur `main` → GitHub Actions déploie automatiquement sur votre VPS

**Architecture** :
- **FastAPI** : API de traitement des documents
- **Docker** : Containerisation de l'application
- **Caddy** : Reverse proxy avec HTTPS automatique
- **GitHub Actions** : CI/CD automatique

---

## 🔧 ÉTAPES DE DÉPLOIEMENT (À faire une seule fois)

### **ÉTAPE 1** - Configurer GitHub Actions

Dans **Settings → Secrets and variables → Actions** de votre repo, ajouter :

| Secret | Description | Exemple |
|--------|-------------|---------|
| `HOST` | IP de votre VPS | `185.xxx.xxx.xxx` |
| `USERNAME` | Utilisateur SSH | `root` ou `ubuntu` |
| `SSH_PRIVATE_KEY` | Clé privée SSH complète | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

**Générer une clé SSH** (si nécessaire) :
```bash
# Sur votre machine locale
ssh-keygen -t ed25519 -f ~/.ssh/ratios_deploy
ssh-copy-id -i ~/.ssh/ratios_deploy.pub root@VOTRE_IP_VPS
cat ~/.ssh/ratios_deploy  # Copier dans SSH_PRIVATE_KEY
```

### **ÉTAPE 2** - Préparer le VPS

```bash
# Se connecter au VPS
ssh root@VOTRE_IP_VPS

# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Installer Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Créer la structure
mkdir -p ~/ratios/data
cd ~/ratios
docker volume create caddy_data
```

### **ÉTAPE 3** - Télécharger les fichiers de configuration

```bash
# Sur le VPS, dans ~/ratios
curl -O https://raw.githubusercontent.com/PolpiFD/ratios_categorisation/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/PolpiFD/ratios_categorisation/main/Caddyfile

# Modifier docker-compose.yml
sed -i 's/\${{ github.repository }}/VOTRE_USERNAME\/ratios_categorisation/g' docker-compose.yml
```

### **ÉTAPE 4** - Créer le fichier .env

```bash
# Sur le VPS
nano ~/ratios/.env
```

Copier ce contenu (remplacer par vos vraies valeurs) :

```bash
# Configuration de l'API
DEBUG=false
WEBHOOK_API_KEY=your-secure-webhook-api-key

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

# OneDrive (legacy - sera remplacé par SharePoint)
DRIVE_ID=your-onedrive-drive-id

# SharePoint (nouvelles variables pour migration depuis OneDrive)
SHAREPOINT_TENANT_ID=your-sharepoint-tenant-id
SHAREPOINT_CLIENT_ID=your-sharepoint-client-id
SHAREPOINT_CLIENT_SECRET=your-sharepoint-client-secret

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# LangSmith (optionnel pour monitoring)
LANGCHAIN_API_KEY=your-langchain-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ratios-categorisation

# Caddy - Email pour Let's Encrypt
CADDY_EMAIL=your-email@gmail.com
```

### **ÉTAPE 5** - Configurer DNS

Pointer votre domaine vers l'IP du VPS :
```
A    @           VOTRE_IP_VPS
A    www         VOTRE_IP_VPS
```

### **ÉTAPE 6** - Premier déploiement

```bash
# Sur votre machine locale (pas le VPS !)
git push origin main
```

**C'est tout !** GitHub Actions va automatiquement :
1. Tester le code
2. Builder l'image Docker
3. La pousser vers GitHub Registry
4. Se connecter au VPS
5. Télécharger et démarrer l'application

---

## 📊 Vérification et Maintenance

### Vérifier que ça marche
```bash
# Statut des conteneurs
docker ps

# Logs de l'application
docker logs ratios-api -f

# Test de l'API
curl https://ratios.futurdigitaln8n.ch/health
```

### Commandes utiles
```bash
# Redémarrer l'application
cd ~/ratios && docker compose restart

# Voir les logs d'erreur
docker logs ratios-api 2>&1 | grep "ERROR"

# Nettoyer les anciennes images
docker image prune -f
```

---

## 🔒 Sécurité (Optionnel mais recommandé)

```bash
# Firewall basique
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

---

## ✅ Checklist de Déploiement

- [ ] Secrets GitHub Actions configurés
- [ ] VPS avec Docker installé
- [ ] DNS pointant vers le VPS
- [ ] Fichiers docker-compose.yml et Caddyfile téléchargés et modifiés
- [ ] Fichier .env créé avec les vraies valeurs
- [ ] Premier push sur main effectué
- [ ] Application accessible via https://ratios.futurdigitaln8n.ch/health

**Après ça, chaque push sur `main` met à jour automatiquement la production !**