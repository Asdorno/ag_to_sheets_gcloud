# AG to Google Sheets Sync

Python pipeline that synchronizes vehicle inventory data from the Auto-Gestion API into a Google Sheet.

The pipeline reads vehicle IDs and update timestamps from the AG API, compares them with the current Google Sheet contents, then updates changed vehicles, appends new vehicles, and deletes vehicles that no longer exist in the API.

## Features

- Fetches vehicle inventory data from the AG API using OAuth1.
- Parses AG XML responses into typed `Vehicle` models.
- Compares API and sheet state using vehicle IDs and `changed_tms` timestamps.
- Updates, creates, and deletes Google Sheets rows in sync with the API.
- Builds feed-ready sheet rows with images, descriptions, prices, labels, and numeric custom fields.
- Reads sensitive configuration from Google Cloud Secret Manager.
- Includes unit tests for parsing, transformation, model validation, and comparison logic.

## Project Structure

```text
.
├── api/                    # Low-level AG API request functions
├── client/                 # API and Google Sheets client wrappers
├── integration/            # Google Sheets operations and row transformation
├── model/                  # Pydantic data models
├── parser/                 # XML parsing and normalization
├── service/                # Sync orchestration and comparison logic
├── tests/                  # Unit tests
├── pipeline.py             # Main pipeline entry point
├── secret_accessor.py      # Google Cloud Secret Manager helper
├── Dockerfile              # Container image definition
└── requirements.txt        # Python dependencies
```

## How It Works

1. `pipeline.py` creates an `APIClient`, `SheetClient`, and `VehicleSyncService`.
2. `VehicleSyncService` loads vehicle ID-to-timestamp mappings from the AG API and from Google Sheets.
3. `compare_vehicles` classifies vehicles into:
   - `to_update`: vehicles present in both systems with different `changed_tms` values
   - `to_create`: vehicles present in the API but missing from the sheet
   - `to_delete`: vehicles present in the sheet but missing from the API
4. Full details are fetched only for vehicles that need to be created or updated.
5. Google Sheets rows are updated, deleted, compacted, or appended as needed.

## Requirements

- Python 3.13
- Access to the AG API
- A Google Cloud project with Secret Manager enabled
- Google credentials with access to:
  - Secret Manager secrets used by this project
  - The target Google Sheet
  - Google Sheets API

## Configuration

The application reads configuration from Google Cloud Secret Manager via `secret_accessor.py`.

Required secrets:

| Secret ID | Purpose |
| --- | --- |
| `AG_API_URL` | Base URL for the AG API |
| `AG_API_CONSUMER_KEY` | OAuth1 consumer key for the AG API |
| `AG_API_CONSUMER_SECRET` | OAuth1 consumer secret for the AG API |
| `SHEET_ID` | Google Sheet spreadsheet ID |

The Google Cloud project ID is resolved dynamically by `secret_accessor.py`. It can come from:

- the default Google authentication context, via Application Default Credentials
- the `GOOGLE_CLOUD_PROJECT` environment variable, which can also be provided through a local `.env` file

```python
projects/{PROJECT_ID}/secrets/{SECRET_ID}/versions/latest
```

This keeps the deployment portable across Google Cloud projects. When deploying to another project, create the same Secret Manager secret IDs in that project and make sure the runtime service account has permission to access them.

## Local Setup

Create and activate a virtual environment:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Authenticate with Google Cloud for local development:

```bash
gcloud auth application-default login
```

Make sure the authenticated account has permission to access the required secrets and the target Google Sheet.

If the project ID is not resolved automatically, set it in the environment or in a local `.env` file:

```bash
GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
```

## Running the Pipeline

Run the sync locally:

```bash
python pipeline.py
```

Expected console output includes the vehicle IDs selected for update, creation, and deletion, followed by:

```text
Pipeline completed!
```

## Running Tests

Run the unit test suite:

```bash
python -m unittest discover tests
```

The tests cover:

- Vehicle model normalization
- XML parser behavior
- Sheet row transformation
- Vehicle comparison logic

## Docker

Build the image:

```bash
docker build -t ag-to-sheets-sync .
```

Run the container:

```bash
docker run --rm ag-to-sheets-sync
```

When running in a container, the runtime environment must provide Google credentials that can access Secret Manager and Google Sheets. On Google Cloud, this is typically handled through the service account attached to the runtime.

## Google Sheet Expectations

The target sheet should contain a header row. At minimum, the sync logic expects these columns to exist:

| Column | Purpose |
| --- | --- |
| `id` | Vehicle ID |
| `changed_tms` | Last changed timestamp from the AG API |

Additional feed columns are generated from vehicle details, including:

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

- The pipeline updates only rows whose `changed_tms` value differs between the API and the sheet.
- Rows deleted from the sheet are followed by a compaction step to remove gaps.
- Vehicle descriptions are generated in French and include core vehicle details plus equipment options.
- The Google Sheet client uses the first worksheet in the spreadsheet: `sheet1`.
