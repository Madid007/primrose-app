# 🌹 PRIM'ROSE RH — Guide de déploiement

## Architecture

```
BeeOne (PDA) → Excel → Upload Admin → API → Dashboard iPhone
```

## Fichiers du projet

| Fichier | Rôle |
|---------|------|
| `main.py` | API FastAPI — cœur du système |
| `processor.py` | Traitement des Excel BeeOne |
| `dashboard_template.html` | Dashboard PWA (votre fichier tableau-bord-rh.html) |
| `requirements.txt` | Dépendances Python |
| `render.yaml` | Configuration déploiement Render.com |

---

## ÉTAPE 1 — Préparer les fichiers (5 min)

1. Renommer votre `tableau-bord-rh.html` en **`dashboard_template.html`**
2. Mettre tous les fichiers dans un dossier `primrose-app/`

---

## ÉTAPE 2 — Créer un compte GitHub (5 min)

1. Aller sur [github.com](https://github.com) → Sign up (gratuit)
2. Créer un nouveau repository : **`primrose-rh`** (public)
3. Uploader tous les fichiers du dossier `primrose-app/`

---

## ÉTAPE 3 — Déployer sur Render.com (10 min)

1. Aller sur [render.com](https://render.com) → Sign up avec votre compte GitHub
2. **New → Web Service**
3. Connecter votre repository GitHub `primrose-rh`
4. Render détecte automatiquement le `render.yaml`
5. Cliquer **Deploy**

**Variables d'environnement à configurer dans Render :**
```
ADMIN_USER  = anass
ADMIN_PASS  = [votre mot de passe pour Anass]
VIEWER_PASS = [mot de passe pour l'équipe de direction]
```

6. Après ~3 minutes : votre URL est prête
   - Ex: `https://primrose-rh.onrender.com`

---

## ÉTAPE 4 — Installer sur iPhone (2 min)

Pour chaque membre de la direction :

1. Ouvrir **Safari** sur iPhone
2. Aller sur `https://primrose-rh.onrender.com/dashboard`
3. Saisir le mot de passe viewer
4. Toucher le bouton **Partager** (carré avec flèche ↑)
5. → **"Sur l'écran d'accueil"**
6. → **"Ajouter"**

L'app 🌹 apparaît sur l'écran d'accueil comme une vraie application !

---

## ÉTAPE 5 — Mise à jour chaque quinzaine (2 min pour Anass)

1. Exporter les 2 fichiers Excel depuis BeeOne
2. Ouvrir Safari → `https://primrose-rh.onrender.com/admin`
3. Saisir identifiants Anass
4. Sélectionner la campagne et la quinzaine
5. Uploader les 2 fichiers
6. Cliquer **Mettre à jour**
7. ✅ Tous les iPhones de la direction voient les nouvelles données

---

## Accès

| Qui | URL | Identifiants |
|-----|-----|-------------|
| **Vous + Direction** | `/dashboard` | viewer_pass |
| **Anass (admin)** | `/admin` | anass + admin_pass |

---

## En cas de problème

Contacter Claude avec les messages d'erreur affichés.
