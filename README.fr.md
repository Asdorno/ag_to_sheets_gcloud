# Synchronisation AG vers Google Sheets

Pipeline Python qui synchronise les données d'inventaire véhicule depuis l'API Auto-Gestion vers une feuille Google Sheets.

Le pipeline lit les IDs véhicule et les timestamps de mise à jour depuis l'API AG, les compare avec le contenu actuel de la feuille Google Sheets, puis met à jour les véhicules modifiés, ajoute les nouveaux véhicules et supprime ceux qui n'existent plus dans l'API.

La feuille Google Sheets générée est pensée pour servir de flux catalogue Meta. Les champs sélectionnés, comme `id`, `title`, `description`, `availability`, `condition`, `price`, `link`, `image_link`, `additional_image_link[...]`, `custom_label_...` et `custom_number_...`, sont construits pour décrire les véhicules dans une structure exploitable par des workflows de catalogue Meta.

## Fonctionnalités

- Récupération des données d'inventaire véhicule depuis l'API AG avec OAuth1.
- Parsing des réponses XML AG vers des modèles `Vehicle` typés.
- Comparaison de l'état API et Google Sheets à partir des IDs véhicule et des timestamps `changed_tms`.
- Mise à jour, création et suppression de lignes Google Sheets.
- Génération de lignes compatibles avec un flux produit, incluant images, descriptions, prix, labels et champs numériques personnalisés.
- Lecture des informations sensibles depuis Google Cloud Secret Manager.
- Tests unitaires pour le parsing, la transformation, la validation du modèle et la logique de comparaison.

## Structure Du Projet

```text
.
├── api/                    # Fonctions bas niveau pour les requêtes à l'API AG
├── client/                 # Wrappers clients pour l'API et Google Sheets
├── integration/            # Opérations Google Sheets et transformation des lignes
├── model/                  # Modèles de données Pydantic
├── parser/                 # Parsing XML et normalisation
├── service/                # Orchestration de la synchronisation et logique de comparaison
├── tests/                  # Tests unitaires
├── pipeline.py             # Point d'entrée principal du pipeline
├── secret_accessor.py      # Helper Google Cloud Secret Manager
├── Dockerfile              # Définition de l'image Docker
└── requirements.txt        # Dépendances Python
```

## Fonctionnement

1. `pipeline.py` crée un `APIClient`, un `SheetClient` et un `VehicleSyncService`.
2. `APIClient` encapsule l'accès à l'API AG et expose des méthodes pour lire les IDs véhicule, les timestamps et les détails complets des véhicules.
3. `SheetClient` encapsule l'accès à Google Sheets et expose des méthodes pour lire les lignes existantes, créer des lignes, mettre à jour des lignes, supprimer des lignes et compacter la feuille.
4. `VehicleSyncService` charge les correspondances ID véhicule/timestamp depuis l'API AG et depuis Google Sheets.
5. `compare_vehicles` classe les véhicules en trois catégories :
   - `to_update` : véhicules présents dans les deux systèmes avec des valeurs `changed_tms` différentes
   - `to_create` : véhicules présents dans l'API mais absents de la feuille
   - `to_delete` : véhicules présents dans la feuille mais absents de l'API
6. Les détails complets sont récupérés uniquement pour les véhicules à créer ou à mettre à jour.
7. Les lignes Google Sheets sont mises à jour, supprimées, compactées ou ajoutées selon le besoin.

## Prérequis

- Python 3.13
- Accès à l'API AG
- Un projet Google Cloud avec Secret Manager activé
- Des identifiants Google avec accès :
  - aux secrets Secret Manager utilisés par ce projet
  - à la feuille Google Sheets cible
  - à l'API Google Sheets

## Estimation Des Coûts

Pour un faible volume de données, ce projet est censé rester largement sous les limites gratuites et les quotas habituels de Google Cloud. Un exemple d'utilisation réelle avec environ 20 véhicules a généré un fichier Google Sheets d'environ 25-50 KB, ce qui reste très loin des volumes où le stockage, les quotas API ou le transfert de données deviennent généralement significatifs.

Limites actuelles à garder en tête :

- Cloud Run Jobs : Google indique un niveau gratuit mensuel de 240 000 vCPU-secondes et 450 000 GiB-secondes, agrégé par compte de facturation.
- Cloud Scheduler : 3 jobs planifiés par mois sont gratuits par compte de facturation ; les exécutions elles-mêmes ne sont pas facturées séparément.
- Secret Manager : 6 versions actives de secrets et 10 000 opérations d'accès par mois sont incluses dans le niveau gratuit.
- Google Sheets API : l'utilisation standard est disponible sans coût supplémentaire, avec des quotas par minute comme 300 requêtes de lecture et 300 requêtes d'écriture par minute et par projet.
- Cloud Build : Google indique 2 500 minutes de build gratuites par mois pour le pool par défaut `e2-standard-2`, sous réserve de changement.
- Artifact Registry : les premiers 0,5 GB d'artefacts stockés sont gratuits ; le transfert de données dans la même localisation ou vers Google Cloud est généralement gratuit.

La facturation doit tout de même être activée pour le déploiement, et les tarifs Google Cloud peuvent changer. Il faut vérifier les pages officielles de tarification avant une mise en production ou une passation.

## Configuration

L'application lit sa configuration depuis Google Cloud Secret Manager via `secret_accessor.py`.

Secrets requis :

| Secret ID | Rôle |
| --- | --- |
| `AG_API_URL` | URL de base de l'API AG |
| `AG_API_CONSUMER_KEY` | Clé consommateur OAuth1 pour l'API AG |
| `AG_API_CONSUMER_SECRET` | Secret consommateur OAuth1 pour l'API AG |
| `SHEET_ID` | ID du spreadsheet Google Sheets |

L'ID du projet Google Cloud est résolu dynamiquement par `secret_accessor.py`. Il peut venir :

- du contexte d'authentification Google par défaut, via Application Default Credentials
- de la variable d'environnement `GOOGLE_CLOUD_PROJECT`, qui peut aussi être fournie via un fichier `.env` local

```python
projects/{PROJECT_ID}/secrets/{SECRET_ID}/versions/latest
```

Cela rend le déploiement portable entre plusieurs projets Google Cloud. Pour déployer vers un autre projet, il faut créer les mêmes Secret IDs dans Secret Manager sur ce projet et vérifier que le compte de service d'exécution dispose des permissions nécessaires pour y accéder.

## Installation Locale

Créer et activer un environnement virtuel :

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

S'authentifier auprès de Google Cloud pour le développement local :

```bash
gcloud auth application-default login
```

Vérifier que le compte authentifié dispose des permissions nécessaires pour accéder aux secrets requis et à la feuille Google Sheets cible.

Si l'ID du projet n'est pas résolu automatiquement, le définir dans l'environnement ou dans un fichier `.env` local :

```bash
GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
```

## Lancer Le Pipeline

Lancer la synchronisation en local :

```bash
python pipeline.py
```

La sortie console attendue contient les IDs véhicule sélectionnés pour mise à jour, création et suppression, puis :

```text
Pipeline completed!
```

## Lancer Les Tests

Exécuter la suite de tests unitaires :

```bash
python -m unittest discover tests
```

Les tests couvrent :

- la normalisation du modèle `Vehicle`
- le comportement du parser XML
- la transformation des lignes pour Google Sheets
- la logique de comparaison des véhicules

## Docker

Construire l'image :

```bash
docker build -t ag-to-sheets-sync .
```

Lancer le conteneur :

```bash
docker run --rm ag-to-sheets-sync
```

Lors de l'exécution dans un conteneur, l'environnement doit fournir des identifiants Google capables d'accéder à Secret Manager et à Google Sheets. Sur Google Cloud, cela est généralement géré par le compte de service attaché à l'environnement d'exécution.

Pour les instructions complètes de déploiement et de planification, voir [RUNBOOK.fr.md](RUNBOOK.fr.md).

## Attentes Pour La Feuille Google Sheets

Le spreadsheet cible peut commencer comme une feuille Google Sheets complètement vide. L'application utilise le premier onglet et crée automatiquement la ligne d'en-tête lors de la première exécution réussie.

Si le premier onglet n'est pas vide, il doit déjà contenir les colonnes d'en-tête requises par le pipeline. Sinon, le job échoue avec une erreur claire au lieu de vider ou d'écraser la feuille.

L'en-tête généré contient au minimum :

| Colonne | Rôle |
| --- | --- |
| `id` | ID du véhicule |
| `changed_tms` | Timestamp de dernière modification depuis l'API AG |

Des colonnes supplémentaires sont générées à partir des détails véhicule, notamment :

- `title`
- `description`
- `availability`
- `condition`
- `price`
- `image_link`
- `additional_image_link[...]`
- `custom_label_...`
- `custom_number_...`

## Notes

- Le pipeline met à jour uniquement les lignes dont la valeur `changed_tms` diffère entre l'API et la feuille.
- Les lignes supprimées de la feuille sont suivies d'une étape de compaction pour retirer les espaces vides.
- Les descriptions véhicule sont générées en français et incluent les informations principales du véhicule ainsi que les options.
- Le client Google Sheets utilise le premier onglet du spreadsheet : `sheet1`.
