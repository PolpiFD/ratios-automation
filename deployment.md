# 🚀 Guide de Déploiement VPS - Ratios Categorisation

## 📋 Vue d'ensemble

Ce projet utilise une architecture complète de déploiement automatisé avec :
- **GitHub Actions** pour CI/CD
- **Docker** et **Docker Compose** pour la containerisation  
- **Caddy** comme reverse proxy avec HTTPS automatique
- **GHCR** (GitHub Container Registry) pour le stockage des images

## 🏗️ Architecture de Déploiement

```
GitHub Push → GitHub Actions → Build Docker Image → Push to GHCR → Deploy to VPS
                    ↓
               Tests automatiques
```

Le workflow GitHub Actions (`/.github/workflows/deploy.yml`) :
1. **Test** : Exécute les tests Python
2. **Build & Push** : Construit l'image Docker et la pousse vers GHCR
3. **Deploy** : Se connecte au VPS via SSH et redémarre l'application

## 🔧 Prérequis VPS

### 1. Configuration initiale du serveur

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation de Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Installation de Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Redémarrer la session pour appliquer les permissions Docker
exit
# Se reconnecter en SSH
```

### 2. Structure des dossiers sur le VPS

```bash
# Créer la structure de dossiers
mkdir -p ~/ratios/data
cd ~/ratios

# Créer le volume persistant pour Caddy (certificats SSL)
docker volume create caddy_data
```

## 🔐 Configuration GitHub Actions

Dans les **Settings → Secrets and variables → Actions** de votre repository, ajoutez :

| Secret | Description | Exemple |
|--------|-------------|---------|
| `HOST` | IP publique de votre VPS | `185.xxx.xxx.xxx` |
| `USERNAME` | Utilisateur SSH du VPS | `ubuntu` ou `root` |
| `SSH_PRIVATE_KEY` | Clé privée SSH (contenu complet) | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

### Génération de la clé SSH (si nécessaire)

```bash
# Sur votre machine locale
ssh-keygen -t ed25519 -f ~/.ssh/ratios_deploy -C "deploy@ratios"

# Copier la clé publique sur le VPS
ssh-copy-id -i ~/.ssh/ratios_deploy.pub user@your-vps-ip

# Ajouter la clé privée dans les secrets GitHub
cat ~/.ssh/ratios_deploy
```

## 🌐 Configuration du domaine

### 1. DNS
Configurez votre nom de domaine pour pointer vers l'IP de votre VPS :
```
A    @           185.xxx.xxx.xxx
A    www         185.xxx.xxx.xxx
```

### 2. Caddyfile
Modifiez le `Caddyfile` avec votre domaine :

```bash
# Sur le VPS, après le premier déploiement
cd ~/ratios
sed -i 's/votre-domaine.com/your-actual-domain.com/g' Caddyfile
```

## 📁 Fichiers de configuration VPS

### 1. Variables d'environnement

Créez le fichier `~/ratios/.env` sur votre VPS :

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

# OneDrive
DRIVE_ID=your-onedrive-drive-id

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# LangSmith (optionnel pour monitoring)
LANGCHAIN_API_KEY=your-langchain-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ratios-categorisation
```

### 2. Docker Compose sur le VPS

Le fichier `docker-compose.yml` sera automatiquement utilisé par GitHub Actions. Il configure :
- **app** : L'API Python FastAPI
- **caddy** : Reverse proxy avec HTTPS automatique

## 🚀 Processus de Déploiement

### Déploiement automatique
1. **Push sur main** → GitHub Actions se déclenche automatiquement
2. L'action build l'image Docker et la pousse vers GHCR
3. L'action se connecte au VPS et redémarre l'application

### Premier déploiement manuel

```bash
# 1. Sur le VPS, récupérer les fichiers de configuration
cd ~/ratios
curl -O https://raw.githubusercontent.com/votre-username/ratios_categorisation/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/votre-username/ratios_categorisation/main/Caddyfile

# 2. Modifier l'image dans docker-compose.yml
sed -i 's/\${{ github.repository }}/votre-username\/ratios_categorisation/g' docker-compose.yml

# 3. Se connecter au registry GitHub
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# 4. Lancer l'application
docker compose up -d
```

## 📊 Monitoring et Maintenance

### Vérification du statut

```bash
# Statut des conteneurs
docker ps

# Logs de l'API
docker logs ratios-api -f

# Logs du proxy
docker logs ratios-proxy -f

# Health check
curl https://your-domain.com/health
```

### Commandes de maintenance

```bash
# Redémarrer l'application
cd ~/ratios
docker compose restart

# Mettre à jour manuellement
docker compose pull
docker compose up -d

# Nettoyer les anciennes images
docker image prune -f

# Voir l'utilisation des ressources
docker stats
```

### Monitoring des logs

```bash
# Logs en temps réel avec horodatage
docker logs ratios-api -f --timestamps

# Logs spifiques avec grep
docker logs ratios-api 2>&1 | grep "ERROR"

# Logs Caddy pour le reverse proxy
docker logs ratios-proxy -f
```

## 🔒 Sécurité

### Mesures implémentées

1. **Dockerfile multi-stage** : Réduit la surface d'attaque
2. **Utilisateur non-root** : L'application s'exécute avec un utilisateur dédié
3. **HTTPS automatique** : Caddy gère les certificats SSL/TLS
4. **Headers de sécurité** : Protection XSS, HSTS, CSP
5. **Rate limiting** : Protection contre les attaques DDoS
6. **Health checks** : Surveillance de l'état de l'application

### Recommandations supplémentaires

```bash
# Firewall basique (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Mise à jour automatique des packages de sécurité
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## 🐛 Dépannage

### Problèmes courants

1. **Container ne démarre pas**
   ```bash
   docker logs ratios-api
   # Vérifier les variables d'environnement dans .env
   ```

2. **Certificat SSL non généré**
   ```bash
   docker logs ratios-proxy
   # Vérifier la configuration DNS du domaine
   ```

3. **API non accessible**
   ```bash
   # Tester directement le container
   curl http://localhost:8000/health
   ```

4. **GitHub Actions échec de déploiement**
   - Vérifier les secrets GitHub
   - Vérifier la connexion SSH au VPS
   - Contrôler les logs de l'action

### Rollback en cas de problème

```bash
# Revenir à l'image précédente
cd ~/ratios
docker tag ghcr.io/votre-username/ratios_categorisation:latest ghcr.io/votre-username/ratios_categorisation:backup
docker pull ghcr.io/votre-username/ratios_categorisation:commit-PREVIOUS_COMMIT_SHA
docker tag ghcr.io/votre-username/ratios_categorisation:commit-PREVIOUS_COMMIT_SHA ghcr.io/votre-username/ratios_categorisation:latest
docker compose up -d
```

## 📈 Optimisations Production

### Performance
- **Multi-stage Docker build** pour des images plus légères
- **Health checks** pour une haute disponibilité
- **Logs rotatifs** pour éviter l'accumulation

### Monitoring avancé (optionnel)
- Intégration avec **LangSmith** pour le monitoring des LLM
- Logs structurés JSON pour l'analyse
- Métriques de performance via les health checks

---

## ✅ Checklist de Déploiement

- [ ] VPS configuré avec Docker et Docker Compose
- [ ] Secrets GitHub Actions configurés
- [ ] DNS pointant vers le VPS
- [ ] Fichier `.env` créé sur le VPS
- [ ] Volume Caddy créé
- [ ] Caddyfile modifié avec le bon domaine
- [ ] Premier push sur main effectué
- [ ] Application accessible via HTTPS
- [ ] Health check fonctionnel

Le déploiement est maintenant entièrement automatisé ! Chaque push sur la branche `main` déclenchera automatiquement la mise à jour de votre application en production.