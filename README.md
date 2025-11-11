# Google Maps Scraper Backend

API Flask pour scraper Google Maps avec Playwright.

## 🚀 Déploiement sur Railway

### Option 1 : Via GitHub (Recommandé)

1. **Créez un nouveau repository GitHub** pour le backend :
   ```bash
   cd backend
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/VOTRE_USERNAME/maps-scraper-backend.git
   git push -u origin main
   ```

2. **Déployez sur Railway** :
   - Allez sur [railway.app](https://railway.app)
   - Cliquez sur "New Project"
   - Sélectionnez "Deploy from GitHub repo"
   - Choisissez votre repository backend
   - Railway détectera automatiquement Python et utilisera `nixpacks.toml`

3. **Configurez les variables d'environnement** (optionnel) :
   - `PORT` est automatiquement défini par Railway

### Option 2 : Via Railway CLI

```bash
# Installer Railway CLI
npm install -g @railway/cli

# Se connecter
railway login

# Créer un nouveau projet
railway init

# Déployer
railway up
```

## 🔗 Après le déploiement

1. **Récupérez l'URL** de votre API Railway (ex: `https://votre-app.railway.app`)

2. **Configurez le frontend** :
   Créez `.env.local` dans le dossier racine :
   ```
   NEXT_PUBLIC_API_URL=https://votre-app.railway.app
   ```

3. **Redéployez le frontend** sur Vercel

## 📡 Endpoints API

- `GET /api/health` - Health check
- `POST /api/scrape` - Démarrer un scraping
- `GET /api/jobs` - Liste des jobs
- `GET /api/jobs/{job_id}` - Statut d'un job
- `GET /api/results/{job_id}` - Résultats d'un job
- `GET /api/results/{job_id}/download` - Télécharger CSV
- `DELETE /api/jobs/{job_id}` - Supprimer un job

## 🧪 Test local

```bash
pip install -r requirements.txt
playwright install chromium
python api.py
```

L'API sera disponible sur `http://localhost:5000`

## ⚠️ Notes importantes

- Railway offre 500 heures gratuites par mois
- Le scraping peut prendre du temps selon le nombre de résultats
- Playwright nécessite des dépendances système (installées automatiquement)
