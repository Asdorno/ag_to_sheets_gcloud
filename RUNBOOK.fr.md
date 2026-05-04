# Guide D'exploitation

Version anglaise : [RUNBOOK.md](RUNBOOK.md)

Ce guide explique comment préparer, déployer et planifier le pipeline de synchronisation AG vers Google Sheets sur Google Cloud.

Le déploiement cible est un Cloud Run Job qui exécute `pipeline.py` depuis une image de conteneur. Cloud Scheduler déclenche le job de manière répétée.

## 1. Avant De Commencer

Avant de créer le déploiement Google Cloud, confirmer ces décisions et identifiants.

### Identifiants Métier Requis

Il faut avoir accès aux identifiants de l'API Auto-Gestion :

- AG API base URL
- AG API consumer key
- AG API consumer secret

Ces valeurs seront stockées dans Google Cloud Secret Manager, et non commit dans GitHub.

### Compte Google Et Décision De Facturation

Décider quel compte Google va posséder ou administrer le projet Google Cloud.

C'est important car le projet doit avoir la facturation activée. En pratique, cela signifie que le compte ou l'organisation qui possède le déploiement doit avoir un compte Cloud Billing valide. Si aucun compte de facturation n'existe encore, Google Cloud demandera des informations de paiement, comme une carte bancaire.

Modèle de propriété recommandé :

- Le compte de l'entreprise ou du manager possède le projet Google Cloud.
- Le projet est lié au compte de facturation de l'entreprise.
- Les développeurs reçoivent les accès IAM nécessaires pour déployer et maintenir le job.
- Le compte de service d'exécution possède uniquement les permissions nécessaires à l'application.

Éviter de déployer des jobs de production à long terme dans un projet Google Cloud personnel si le projet doit survivre après un stage ou un changement d'employé.

### Google Sheet Requis

Créer un document Google Sheets complètement vide avant le déploiement.

Configuration recommandée :

1. Créer une nouvelle feuille Google Sheet.
2. Copier l'ID du spreadsheet depuis l'URL.

Exemple d'URL :

```text
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

3. Laisser le premier onglet vide. Ne pas ajouter d'en-têtes manuellement.
4. Après avoir créé le compte de service d'exécution Cloud Run, partager la feuille avec l'email de ce compte de service et lui donner la permission Editor.

L'application utilise le premier onglet du spreadsheet. Lors de la première exécution réussie, elle crée automatiquement la ligne d'en-tête puis ajoute les données véhicule.

Si le premier onglet n'est pas vide et ne contient pas les colonnes d'en-tête requises par le pipeline, le job échoue avec une erreur claire au lieu de vider ou d'écraser la feuille. Cela évite une perte accidentelle de données si le mauvais spreadsheet ID est configuré.

## 2. Installer Les Outils Locaux

Installer ces outils sur la machine utilisée pour le déploiement :

- Git
- Google Cloud CLI

Liens d'installation officiels :

- Git: https://git-scm.com/install/
- Google Cloud CLI: https://docs.cloud.google.com/sdk/docs/install

Docker n'est pas requis pour le chemin de déploiement Google Cloud recommandé. Ce runbook construit l'image de conteneur avec Google Cloud Build et la déploie sur Cloud Run. Installer Docker uniquement si vous voulez aussi exécuter le conteneur localement, construire les images manuellement ou déployer le projet sur votre propre serveur.

Liens d'installation Docker optionnels :

- Docker Desktop: https://docs.docker.com/get-started/introduction/get-docker-desktop/
- Docker Engine: https://docs.docker.com/en/latest/installation/

Vérifier les outils :

```bash
git --version
gcloud --version
```

Sur Windows PowerShell :

```powershell
git --version
gcloud --version
```

## 3. Récupérer Le Projet Depuis GitHub

Choisir un dossier de travail local, puis cloner le dépôt.

Linux/macOS :

```bash
cd ~/projects
git clone https://github.com/Asdorno/ag_to_sheets_gcloud.git
cd ag_to_sheets_gcloud
```

Windows PowerShell :

```powershell
cd $HOME\projects
git clone https://github.com/Asdorno/ag_to_sheets_gcloud.git
cd ag_to_sheets_gcloud
```

Vérifier l'état du dépôt :

```bash
git status
git remote -v
```

Configuration optionnelle pour les tests locaux :

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover tests
```

Windows PowerShell :

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m unittest discover tests
```

## 4. Créer Ou Sélectionner Un Projet Google Cloud

Google Cloud utilise deux ressources séparées ici :

- Un projet Google Cloud, qui contient Cloud Run, Secret Manager, Artifact Registry, Cloud Scheduler et les ressources IAM.
- Un compte Cloud Billing, qui paie l'utilisation et doit être lié au projet.

S'il s'agit d'un tout nouveau compte Google Cloud, créer ou activer d'abord le compte Cloud Billing dans la Google Cloud Console. La CLI peut créer et sélectionner le projet, mais la première configuration du compte de facturation nécessite généralement l'interface web parce que Google demande les informations du profil de paiement, le pays/la devise, les informations fiscales si applicable, et un moyen de paiement comme une carte bancaire. Les nouveaux utilisateurs Google Cloud peuvent aussi être invités à démarrer un essai gratuit avec des crédits offerts, mais le projet a tout de même besoin d'un compte Cloud Billing actif lié au projet.

Définir les variables de déploiement. Remplacer les valeurs par les choix finaux de production.

Linux/macOS :

```bash
export PROJECT_ID="your-project-id"
export PROJECT_NAME="AG to Sheets Sync"
export REGION="europe-west1"
export REPOSITORY="ag-to-sheets"
export IMAGE_NAME="ag-to-sheets-sync"
export JOB_NAME="ag-to-sheets-sync"
export SCHEDULER_JOB_NAME="ag-to-sheets-sync-schedule"
export RUNTIME_SA_NAME="ag-to-sheets-runner"
export SCHEDULER_SA_NAME="ag-to-sheets-scheduler"
```

Windows PowerShell :

```powershell
$env:PROJECT_ID = "your-project-id"
$env:PROJECT_NAME = "AG to Sheets Sync"
$env:REGION = "europe-west1"
$env:REPOSITORY = "ag-to-sheets"
$env:IMAGE_NAME = "ag-to-sheets-sync"
$env:JOB_NAME = "ag-to-sheets-sync"
$env:SCHEDULER_JOB_NAME = "ag-to-sheets-sync-schedule"
$env:RUNTIME_SA_NAME = "ag-to-sheets-runner"
$env:SCHEDULER_SA_NAME = "ag-to-sheets-scheduler"
```

S'authentifier avec Google Cloud :

```bash
gcloud auth login
gcloud auth application-default login
```

### Créer Ou Confirmer Le Compte Cloud Billing

Faire cette étape avant d'aller trop loin dans le déploiement. Sans facturation, les étapes suivantes comme l'activation des services, la construction avec Cloud Build, l'envoi vers Artifact Registry ou l'exécution des Cloud Run Jobs peuvent échouer ou rester inutilisables.

Flux recommandé pour une première configuration :

1. Ouvrir la Google Cloud Console : https://console.cloud.google.com/
2. Se connecter avec le compte Google qui doit posséder ou administrer le déploiement.
3. Ouvrir Billing : https://console.cloud.google.com/billing
4. S'il n'y a pas de compte Cloud Billing, choisir l'option pour en créer un.
5. Saisir le nom du compte de facturation.
6. Sélectionner le pays et la devise avec attention. Google indique que ces choix affectent les options de paiement et ne peuvent généralement pas être modifiés plus tard pour ce compte de facturation.
7. Créer ou sélectionner le profil Google payments.
8. Ajouter le moyen de paiement demandé, comme une carte bancaire.
9. Si Google propose un essai gratuit ou des crédits offerts pour ce compte, suivre les étapes pour l'activer si c'est approprié.
10. Valider et activer la facturation.

Pour un déploiement d'entreprise, utiliser le compte/profil de paiement de l'entreprise ou du manager plutôt qu'un compte personnel d'étudiant ou de stagiaire. La personne qui crée le compte de facturation en est généralement administratrice, donc il faut s'assurer que la propriété restera disponible après la passation.

Documentation officielle sur la facturation :

- Create a Cloud Billing account: https://cloud.google.com/billing/docs/how-to/create-billing-account
- Manage Cloud Billing accounts: https://cloud.google.com/billing/docs/how-to/manage-billing-account
- Enable or change billing for a project: https://cloud.google.com/billing/docs/how-to/modify-project
- Verify billing status: https://docs.cloud.google.com/billing/docs/how-to/verify-billing-enabled

Une fois le compte de facturation créé, continuer avec la création du projet.

Créer le projet :

```bash
gcloud projects create "$PROJECT_ID" --name="$PROJECT_NAME"
gcloud config set project "$PROJECT_ID"
```

Windows PowerShell :

```powershell
gcloud projects create $env:PROJECT_ID --name="$env:PROJECT_NAME"
gcloud config set project $env:PROJECT_ID
```

Si le projet existe déjà, le sélectionner simplement :

```bash
gcloud config set project "$PROJECT_ID"
```

### Activer La Facturation

La facturation est activée sur un projet uniquement lorsque le projet est lié à un compte Cloud Billing actif. Créer un projet avec `gcloud projects create` ne lie pas forcément la facturation automatiquement.

Lister les comptes de facturation accessibles par le compte Google actuel :

```bash
gcloud billing accounts list
```

La sortie contient des IDs de compte de facturation dans ce format :

```text
XXXXXX-XXXXXX-XXXXXX
```

Si la liste est vide, le compte connecté n'a pas accès à un compte de facturation. Revenir à la configuration Billing dans la Console ci-dessus, ou demander à l'administrateur de facturation de l'entreprise de créer un compte de facturation et de vous donner la permission d'y lier des projets.

Lier le projet au compte de facturation :

```bash
gcloud billing projects link "$PROJECT_ID" --billing-account="BILLING_ACCOUNT_ID"
```

Windows PowerShell :

```powershell
gcloud billing projects link $env:PROJECT_ID --billing-account="BILLING_ACCOUNT_ID"
```

Vérifier que la facturation est activée :

```bash
gcloud billing projects describe "$PROJECT_ID"
```

Windows PowerShell :

```powershell
gcloud billing projects describe $env:PROJECT_ID
```

Chercher `billingEnabled: true`. Si la facturation n'est pas activée, Cloud Run, Cloud Build, Artifact Registry et Scheduler peuvent ne pas fonctionner correctement.

Il est aussi possible de vérifier la facturation dans la Console :

1. Ouvrir https://console.cloud.google.com/billing
2. Sélectionner le projet.
3. Confirmer qu'il est lié au bon compte Cloud Billing.

### Utilisation Prévue Et Contexte Des Limites Gratuites

La facturation doit être activée, mais ce projet est conçu pour de petits jobs de synchronisation planifiés et un faible volume de données. Avec des tailles d'inventaire classiques pour un garage, il devrait rester largement sous les limites gratuites et les quotas API habituels.

Exemple d'utilisation réelle :

- Environ 20 véhicules enregistrés.
- Taille du fichier Google Sheets généré : environ 25-50 KB.
- Une exécution planifiée effectue généralement un petit nombre de lectures Secret Manager, de requêtes API AG, de lectures/écritures Google Sheets et de secondes d'exécution Cloud Run.

Limites Google Cloud actuelles à garder en tête :

| Service | Détail actuel du niveau gratuit ou quota | Pourquoi ce projet devrait rester à faible volume |
| --- | --- | --- |
| Cloud Run Jobs | Le niveau gratuit mensuel inclut 240 000 vCPU-secondes et 450 000 GiB-secondes, agrégé par compte de facturation. | Un job Python planifié devrait normalement tourner pendant quelques secondes ou minutes, pas en continu. |
| Cloud Scheduler | 3 jobs planifiés sont gratuits par compte de facturation ; les exécutions elles-mêmes ne sont pas facturées séparément. | Ce déploiement a besoin d'un seul job Scheduler. |
| Secret Manager | Le niveau gratuit inclut 6 versions actives de secrets et 10 000 opérations d'accès par mois. | Ce projet utilise 4 secrets et les lit uniquement quand le job s'exécute. |
| Google Sheets API | L'utilisation standard est disponible sans coût supplémentaire ; les quotas fréquents incluent 300 requêtes de lecture et 300 requêtes d'écriture par minute et par projet. | Un petit inventaire véhicule produit peu d'opérations sur la feuille. |
| Cloud Build | Google indique 2 500 minutes de build gratuites par mois pour le pool par défaut `e2-standard-2`, sous réserve de changement. | Les builds ont lieu uniquement lors du déploiement d'une nouvelle image, pas à chaque exécution planifiée. |
| Artifact Registry | Les premiers 0,5 GB de stockage sont gratuits ; le transfert de données vers Google Cloud et dans la même localisation est généralement gratuit. | L'image de conteneur et les données de feuille sont petites. |

Points importants :

- Les niveaux gratuits sont généralement calculés par compte de facturation, pas uniquement par projet.
- Certains niveaux gratuits dépendent de la région ou sont appliqués comme remises selon la tarification régionale.
- Le transfert sortant vers Internet peut être facturé selon la source, la destination et le volume.
- Les prix et quotas peuvent changer, donc vérifier les pages officielles pendant la passation.

Pour ce projet, le principal contrôle opérationnel des coûts consiste à garder une planification raisonnable, par exemple une fois par jour ou quelques fois par jour, sauf si le besoin métier exige explicitement des mises à jour plus fréquentes.

### Créer Une Alerte Budget De 10 EUR

Créer un budget avant de déployer le job planifié. Cela ne crée pas un plafond dur de dépenses, mais envoie des emails d'alerte lorsque le projet atteint les seuils configurés. Les frais Google Cloud peuvent être reportés avec un certain délai, donc il ne faut pas considérer le budget comme un mécanisme d'arrêt automatique.

Budget recommandé :

| Paramètre | Valeur |
| --- | --- |
| Budget amount | `10 EUR` |
| Budget period | Monthly |
| Scope | This project only |
| Alert thresholds | 50%, 80%, 100% |
| Trigger type | Actual spend |

Activer la Billing Budgets API :

```bash
gcloud services enable billingbudgets.googleapis.com
```

Windows PowerShell :

```powershell
gcloud services enable billingbudgets.googleapis.com
```

Trouver l'ID du compte de facturation :

```bash
gcloud billing accounts list
```

L'ID du compte de facturation a ce format :

```text
XXXXXX-XXXXXX-XXXXXX
```

Le définir comme variable.

Linux/macOS :

```bash
export BILLING_ACCOUNT_ID="XXXXXX-XXXXXX-XXXXXX"
```

Windows PowerShell :

```powershell
$env:BILLING_ACCOUNT_ID = "XXXXXX-XXXXXX-XXXXXX"
```

Créer le budget avec des alertes à 50%, 80% et 100% des dépenses réelles.

Linux/macOS :

```bash
gcloud billing budgets create \
  --billing-account="$BILLING_ACCOUNT_ID" \
  --display-name="AG to Sheets monthly budget" \
  --budget-amount=10EUR \
  --calendar-period=month \
  --filter-projects="projects/$PROJECT_ID" \
  --threshold-rule=percent=0.50,basis=current-spend \
  --threshold-rule=percent=0.80,basis=current-spend \
  --threshold-rule=percent=1.00,basis=current-spend
```

Windows PowerShell :

```powershell
gcloud billing budgets create `
  --billing-account=$env:BILLING_ACCOUNT_ID `
  --display-name="AG to Sheets monthly budget" `
  --budget-amount=10EUR `
  --calendar-period=month `
  --filter-projects="projects/$env:PROJECT_ID" `
  --threshold-rule=percent=0.50,basis=current-spend `
  --threshold-rule=percent=0.80,basis=current-spend `
  --threshold-rule=percent=1.00,basis=current-spend
```

Vérifier le budget :

```bash
gcloud billing budgets list --billing-account="$BILLING_ACCOUNT_ID"
```

Windows PowerShell :

```powershell
gcloud billing budgets list --billing-account=$env:BILLING_ACCOUNT_ID
```

Par défaut, Google Cloud envoie les emails d'alerte budget aux destinataires IAM du compte de facturation. Ne pas utiliser `--disable-default-iam-recipients` sauf si un autre canal de notification est configuré.

Si la devise du compte de facturation n'est pas EUR, `--budget-amount=10EUR` peut échouer. Utiliser alors la devise du compte de facturation, par exemple `--budget-amount=10USD`, ou l'équivalent local de 10 EUR.

Permissions nécessaires :

- Pour créer un budget sur le compte Cloud Billing, l'utilisateur a généralement besoin du rôle Billing Account Administrator ou Billing Account Costs Manager.
- Si l'utilisateur a uniquement des accès au niveau projet, il peut parfois créer un budget limité aux projets qu'il possède, selon ses permissions projet.

Documentation officielle : https://cloud.google.com/billing/docs/how-to/budgets

## 5. Activer Les APIs Requises

Activer les APIs Google Cloud utilisées par le déploiement.

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  billingbudgets.googleapis.com \
  sheets.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com
```

Windows PowerShell :

```powershell
gcloud services enable `
  run.googleapis.com `
  artifactregistry.googleapis.com `
  cloudbuild.googleapis.com `
  cloudscheduler.googleapis.com `
  secretmanager.googleapis.com `
  billingbudgets.googleapis.com `
  sheets.googleapis.com `
  iam.googleapis.com `
  cloudresourcemanager.googleapis.com
```

## 6. Créer Les Comptes De Service

Créer un compte de service pour l'exécution du Cloud Run Job et un compte de service pour Cloud Scheduler.

Linux/macOS :

```bash
gcloud iam service-accounts create "$RUNTIME_SA_NAME" \
  --display-name="AG to Sheets runtime"

gcloud iam service-accounts create "$SCHEDULER_SA_NAME" \
  --display-name="AG to Sheets scheduler"

export PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
export RUNTIME_SA_EMAIL="$RUNTIME_SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
export SCHEDULER_SA_EMAIL="$SCHEDULER_SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
```

Windows PowerShell :

```powershell
gcloud iam service-accounts create $env:RUNTIME_SA_NAME `
  --display-name="AG to Sheets runtime"

gcloud iam service-accounts create $env:SCHEDULER_SA_NAME `
  --display-name="AG to Sheets scheduler"

$env:PROJECT_NUMBER = gcloud projects describe $env:PROJECT_ID --format="value(projectNumber)"
$env:RUNTIME_SA_EMAIL = "$env:RUNTIME_SA_NAME@$env:PROJECT_ID.iam.gserviceaccount.com"
$env:SCHEDULER_SA_EMAIL = "$env:SCHEDULER_SA_NAME@$env:PROJECT_ID.iam.gserviceaccount.com"
```

Donner au compte de service d'exécution la permission de lire les secrets :

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

Windows PowerShell :

```powershell
gcloud projects add-iam-policy-binding $env:PROJECT_ID `
  --member="serviceAccount:$env:RUNTIME_SA_EMAIL" `
  --role="roles/secretmanager.secretAccessor"
```

Partager la Google Sheet cible avec l'email du compte de service d'exécution et lui donner la permission Editor :

```text
ag-to-sheets-runner@PROJECT_ID.iam.gserviceaccount.com
```

Cette étape de partage du spreadsheet est nécessaire parce que les permissions des documents Google Sheets ne sont pas contrôlées uniquement par Google Cloud IAM.

## 7. Créer Les Secrets Secret Manager

Créer les secrets requis.

Linux/macOS :

```bash
printf "%s" "https://your-ag-api-base-url" | gcloud secrets create AG_API_URL --data-file=-
printf "%s" "your-consumer-key" | gcloud secrets create AG_API_CONSUMER_KEY --data-file=-
printf "%s" "your-consumer-secret" | gcloud secrets create AG_API_CONSUMER_SECRET --data-file=-
printf "%s" "your-google-sheet-id" | gcloud secrets create SHEET_ID --data-file=-
```

Windows PowerShell :

```powershell
"https://your-ag-api-base-url" | gcloud secrets create AG_API_URL --data-file=-
"your-consumer-key" | gcloud secrets create AG_API_CONSUMER_KEY --data-file=-
"your-consumer-secret" | gcloud secrets create AG_API_CONSUMER_SECRET --data-file=-
"your-google-sheet-id" | gcloud secrets create SHEET_ID --data-file=-
```

Pour mettre à jour un secret existant plus tard, ajouter une nouvelle version :

```bash
printf "%s" "new-value" | gcloud secrets versions add SECRET_ID --data-file=-
```

Windows PowerShell :

```powershell
"new-value" | gcloud secrets versions add SECRET_ID --data-file=-
```

## 8. Construire Et Publier L'image De Conteneur Avec Google Cloud Build

Utiliser Google Cloud Build pour le déploiement standard. Cela rend le déploiement indépendant de la machine locale et évite d'avoir Docker installé localement.

Créer un dépôt Docker Artifact Registry :

```bash
gcloud artifacts repositories create "$REPOSITORY" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Container images for AG to Sheets sync"
```

Windows PowerShell :

```powershell
gcloud artifacts repositories create $env:REPOSITORY `
  --repository-format=docker `
  --location=$env:REGION `
  --description="Container images for AG to Sheets sync"
```

Construire et publier l'image avec Cloud Build :

Linux/macOS :

```bash
export IMAGE_URI="$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$IMAGE_NAME:latest"
gcloud builds submit --tag "$IMAGE_URI"
```

Windows PowerShell :

```powershell
$env:IMAGE_URI = "${env:REGION}-docker.pkg.dev/${env:PROJECT_ID}/${env:REPOSITORY}/${env:IMAGE_NAME}:latest"
gcloud builds submit --tag $env:IMAGE_URI
```

Build Docker local optionnel :

À utiliser uniquement si vous voulez spécifiquement construire l'image sur votre propre machine, tester le conteneur localement ou déployer en dehors de Google Cloud. Pour le déploiement Cloud Run Job normal, utiliser les commandes Cloud Build ci-dessus.

```bash
docker build -t "$IMAGE_URI" .
gcloud auth configure-docker "$REGION-docker.pkg.dev"
docker push "$IMAGE_URI"
```

## 9. Déployer Le Cloud Run Job

Créer le Cloud Run Job avec le compte de service d'exécution.

Linux/macOS :

```bash
gcloud run jobs create "$JOB_NAME" \
  --image="$IMAGE_URI" \
  --region="$REGION" \
  --service-account="$RUNTIME_SA_EMAIL" \
  --tasks=1 \
  --max-retries=1 \
  --task-timeout=30m
```

Windows PowerShell :

```powershell
gcloud run jobs create $env:JOB_NAME `
  --image=$env:IMAGE_URI `
  --region=$env:REGION `
  --service-account=$env:RUNTIME_SA_EMAIL `
  --tasks=1 `
  --max-retries=1 `
  --task-timeout=30m
```

Pour les déploiements suivants, mettre à jour le job existant :

```bash
gcloud run jobs update "$JOB_NAME" \
  --image="$IMAGE_URI" \
  --region="$REGION" \
  --service-account="$RUNTIME_SA_EMAIL"
```

Tester le job manuellement :

```bash
gcloud run jobs execute "$JOB_NAME" --region="$REGION" --wait
```

Vérifier quel compte de service est utilisé par le job :

```bash
gcloud run jobs describe "$JOB_NAME" \
  --region="$REGION" \
  --format="value(template.template.serviceAccount)"
```

Lire les logs :

```bash
gcloud logging read \
  "resource.type=\"cloud_run_job\" AND resource.labels.job_name=\"$JOB_NAME\"" \
  --limit=50 \
  --format="value(textPayload)"
```

## 10. Configurer Cloud Scheduler

Cloud Scheduler va appeler l'endpoint de l'API Cloud Run Jobs qui exécute le job.

Donner au compte de service Scheduler la permission d'exécuter des Cloud Run jobs :

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SCHEDULER_SA_EMAIL" \
  --role="roles/run.invoker"
```

Windows PowerShell :

```powershell
gcloud projects add-iam-policy-binding $env:PROJECT_ID `
  --member="serviceAccount:$env:SCHEDULER_SA_EMAIL" `
  --role="roles/run.invoker"
```

Créer le job Scheduler. Cet exemple s'exécute tous les jours à 06:00 heure Europe/Paris.

Linux/macOS :

```bash
gcloud scheduler jobs create http "$SCHEDULER_JOB_NAME" \
  --location="$REGION" \
  --schedule="0 6 * * *" \
  --time-zone="Europe/Paris" \
  --uri="https://run.googleapis.com/v2/projects/$PROJECT_ID/locations/$REGION/jobs/$JOB_NAME:run" \
  --http-method=POST \
  --oauth-service-account-email="$SCHEDULER_SA_EMAIL"
```

Windows PowerShell :

```powershell
gcloud scheduler jobs create http $env:SCHEDULER_JOB_NAME `
  --location=$env:REGION `
  --schedule="0 6 * * *" `
  --time-zone="Europe/Paris" `
  --uri="https://run.googleapis.com/v2/projects/${env:PROJECT_ID}/locations/${env:REGION}/jobs/${env:JOB_NAME}:run" `
  --http-method=POST `
  --oauth-service-account-email=$env:SCHEDULER_SA_EMAIL
```

Déclencher la planification manuellement :

```bash
gcloud scheduler jobs run "$SCHEDULER_JOB_NAME" --location="$REGION"
```

Windows PowerShell :

```powershell
gcloud scheduler jobs run $env:SCHEDULER_JOB_NAME --location=$env:REGION
```

## 11. Vérifications Opérationnelles

Après le déploiement, vérifier toute la chaîne :

1. Cloud Scheduler existe et possède la planification attendue.
2. Cloud Scheduler peut déclencher le Cloud Run Job.
3. Le Cloud Run Job utilise le compte de service d'exécution dédié.
4. Le compte de service d'exécution possède `roles/secretmanager.secretAccessor`.
5. Le compte de service d'exécution a un accès Editor à la Google Sheet.
6. Secret Manager contient ces secrets :
   - `AG_API_URL`
   - `AG_API_CONSUMER_KEY`
   - `AG_API_CONSUMER_SECRET`
   - `SHEET_ID`
7. La Google Sheet est soit complètement vide avant la première exécution, soit déjà initialisée par une exécution réussie précédente du pipeline.
8. Une exécution manuelle du job se termine avec succès.

Commandes utiles :

```bash
gcloud scheduler jobs describe "$SCHEDULER_JOB_NAME" --location="$REGION"
gcloud run jobs describe "$JOB_NAME" --region="$REGION"
gcloud secrets list
gcloud run jobs executions list --job="$JOB_NAME" --region="$REGION"
```

## 12. Problèmes Courants

### Permission denied when reading secrets

Le compte de service d'exécution n'a pas accès à Secret Manager.

Correction :

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

### Permission denied when editing Google Sheets

La Google Sheet n'a pas été partagée avec le compte de service d'exécution.

Correction :

1. Ouvrir la Google Sheet.
2. Cliquer sur Share.
3. Ajouter l'email du compte de service d'exécution.
4. Accorder la permission Editor.

### Scheduler cannot trigger the job

Le compte de service Scheduler n'a pas la permission d'invoquer les Cloud Run jobs.

Correction :

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SCHEDULER_SA_EMAIL" \
  --role="roles/run.invoker"
```

### Wrong Google Cloud project is used

Vérifier le projet courant :

```bash
gcloud config get-value project
```

Le définir explicitement :

```bash
gcloud config set project "$PROJECT_ID"
```

L'application résout elle-même l'ID du projet depuis l'authentification Google par défaut ou depuis `GOOGLE_CLOUD_PROJECT`.

## Références

- Cloud Run jobs service identity: https://docs.cloud.google.com/run/docs/configuring/jobs/service-identity
- Execute Cloud Run jobs on a schedule: https://docs.cloud.google.com/run/docs/execute/jobs-on-schedule
- Cloud Scheduler HTTP jobs: https://docs.cloud.google.com/sdk/gcloud/reference/scheduler/jobs/create/http
- Secret Manager versions: https://docs.cloud.google.com/secret-manager/docs/add-secret-version
- Cloud Billing for projects: https://docs.cloud.google.com/billing/docs/how-to/modify-project
- Cloud Billing budgets and alerts: https://cloud.google.com/billing/docs/how-to/budgets
- Cloud Run pricing and free tier: https://cloud.google.com/run/pricing
- Cloud Scheduler pricing: https://cloud.google.com/scheduler/pricing
- Secret Manager pricing: https://cloud.google.com/secret-manager/pricing
- Google Sheets API usage limits: https://developers.google.com/workspace/sheets/api/limits
- Cloud Build pricing: https://cloud.google.com/build/pricing
- Artifact Registry pricing: https://cloud.google.com/artifact-registry/pricing
