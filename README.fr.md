# Synchronisation AG vers Google Sheets

Pipeline Python qui synchronise les données d'inventaire véhicule depuis l'API Auto-Gestion vers une feuille Google Sheets.

Le pipeline lit les IDs véhicule et les timestamps de mise à jour depuis l'API AG, les compare avec le contenu actuel de la feuille Google Sheets, puis met à jour les véhicules modifiés, ajoute les nouveaux véhicules et supprime ceux qui n'existent plus dans l'API.

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
2. `VehicleSyncService` charge les correspondances ID véhicule/timestamp depuis l'API AG et depuis Google Sheets.
3. `compare_vehicles` classe les véhicules en trois catégories :
   - `to_update` : véhicules présents dans les deux systèmes avec des valeurs `changed_tms` différentes
   - `to_create` : véhicules présents dans l'API mais absents de la feuille
   - `to_delete` : véhicules présents dans la feuille mais absents de l'API
4. Les détails complets sont récupérés uniquement pour les véhicules à créer ou à mettre à jour.
5. Les lignes Google Sheets sont mises à jour, supprimées, compactées ou ajoutées selon le besoin.

## Prérequis

- Python 3.13
- Accès à l'API AG
- Un projet Google Cloud avec Secret Manager activé
- Des identifiants Google avec accès :
  - aux secrets Secret Manager utilisés par ce projet
  - à la feuille Google Sheets cible
  - à l'API Google Sheets

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

## Attentes Pour La Feuille Google Sheets

La feuille cible doit contenir une ligne d'en-tête. Au minimum, la logique de synchronisation attend ces colonnes :

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
