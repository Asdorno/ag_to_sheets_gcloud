# Operations Runbook

French version: [RUNBOOK.fr.md](RUNBOOK.fr.md)

This guide explains how to prepare, deploy, and schedule the AG to Google Sheets sync pipeline on Google Cloud.

The target deployment is a Cloud Run Job that runs `pipeline.py` from a container image. Cloud Scheduler triggers the job repeatedly.

The job also rewrites a vehicle JSON export in Google Cloud Storage whenever the AG inventory changes. That JSON file is intended for a separate Telegram bot job.

## 1. Before You Start

Before creating the Google Cloud deployment, confirm these decisions and credentials.

### Required Business Credentials

You need access to the Auto-Gestion API credentials:

- AG API base URL
- AG API consumer key
- AG API consumer secret

These values will be stored in Google Cloud Secret Manager, not committed to GitHub.

### Required Google Account And Billing Decision

Decide which Google account will own or administer the Google Cloud project.

This matters because the project needs billing enabled. In practice, that means the account or organization that owns the deployment must have a valid Cloud Billing account. If no billing account exists yet, Google Cloud will ask for payment information such as a credit card.

Recommended ownership model:

- The company or manager account owns the Google Cloud project.
- The project is linked to the company billing account.
- Developers receive IAM access to deploy and maintain the job.
- The runtime service account owns only the permissions required by the application.

Avoid deploying long-term production jobs in a personal Google Cloud project if the project will need to survive after an internship or employee transition.

### Required Google Sheet

Create a completely empty Google Sheets document before deploying.

Recommended setup:

1. Create a new Google Sheet.
2. Copy the spreadsheet ID from the URL.

Example URL:

```text
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

3. Leave the first worksheet empty. Do not add headers manually.
4. After creating the Cloud Run runtime service account, share the sheet with that service account email and give it Editor permission.

The application uses the first worksheet in the spreadsheet. On the first successful run, it automatically creates the header row and then appends the vehicle data.

If the first worksheet is not empty and does not contain the required pipeline header columns, the job fails with a clear error instead of clearing or overwriting the sheet. This prevents accidental data loss if the wrong spreadsheet ID is configured.

## 2. Install Local Tools

Install these tools on the machine used for deployment:

- Git
- Google Cloud CLI

Official installation links:

- Git: https://git-scm.com/install/
- Google Cloud CLI: https://docs.cloud.google.com/sdk/docs/install

Docker is not required for the recommended Google Cloud deployment path. This runbook builds the container image with Google Cloud Build and deploys it to Cloud Run. Install Docker only if you also want to run the container locally, build images manually, or deploy the project on your own server.

Optional Docker installation links:

- Docker Desktop: https://docs.docker.com/get-started/introduction/get-docker-desktop/
- Docker Engine: https://docs.docker.com/en/latest/installation/

Verify the tools:

```bash
git --version
gcloud --version
```

On Windows PowerShell:

```powershell
git --version
gcloud --version
```

## 3. Pull The Project From GitHub

Choose a local working directory, then clone the repository.

Linux/macOS:

```bash
cd ~/projects
git clone https://github.com/Asdorno/ag_to_sheets_gcloud.git
cd ag_to_sheets_gcloud
```

Windows PowerShell:

```powershell
cd $HOME\projects
git clone https://github.com/Asdorno/ag_to_sheets_gcloud.git
cd ag_to_sheets_gcloud
```

Check the repository state:

```bash
git status
git remote -v
```

Optional local test setup:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover tests
```

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m unittest discover tests
```

## 4. Create Or Select A Google Cloud Project

Google Cloud uses two separate resources here:

- A Google Cloud project, which contains Cloud Run, Secret Manager, Artifact Registry, Cloud Scheduler, and IAM resources.
- A Cloud Billing account, which pays for usage and must be linked to the project.

If this is a brand-new Google Cloud account, create or activate the Cloud Billing account first in the Google Cloud Console. The CLI can create and select the project, but the first billing account setup usually requires the web UI because Google needs payment profile details, country/currency, tax details when applicable, and a payment method such as a credit card. New Google Cloud users may also be prompted to start a free trial with free credits, but the project still needs an active Cloud Billing account linked to it.

Set deployment variables. Replace the values with the final production choices.

Linux/macOS:

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
export GCS_BUCKET_NAME="your-globally-unique-bucket-name"
```

Windows PowerShell:

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
$env:GCS_BUCKET_NAME = "your-globally-unique-bucket-name"
```

Authenticate with Google Cloud:

```bash
gcloud auth login
gcloud auth application-default login
```

### Create Or Confirm The Cloud Billing Account

Do this before going too far with deployment. Without billing, later steps such as enabling services, building with Cloud Build, pushing to Artifact Registry, or running Cloud Run jobs can fail or remain unusable.

Recommended first-time flow:

1. Open the Google Cloud Console: https://console.cloud.google.com/
2. Sign in with the Google account that should own or administer the deployment.
3. Open Billing: https://console.cloud.google.com/billing
4. If there is no Cloud Billing account, choose the option to create one.
5. Enter the billing account name.
6. Select the country and currency carefully. Google notes that these choices affect payment options and generally cannot be changed later for that billing account.
7. Create or select the Google payments profile.
8. Add the requested payment method, such as a credit card.
9. If Google offers a free trial or free credits for this account, follow the prompts to activate it if appropriate.
10. Submit and enable billing.

For a company deployment, use the company or manager account/payment profile rather than a personal student or intern account. The person who creates the billing account is normally an administrator for it, so make sure ownership will remain available after handover.

Official billing setup documentation:

- Create a Cloud Billing account: https://cloud.google.com/billing/docs/how-to/create-billing-account
- Manage Cloud Billing accounts: https://cloud.google.com/billing/docs/how-to/manage-billing-account
- Enable or change billing for a project: https://cloud.google.com/billing/docs/how-to/modify-project
- Verify billing status: https://docs.cloud.google.com/billing/docs/how-to/verify-billing-enabled

After the billing account exists, continue with project creation.

Create the project:

```bash
gcloud projects create "$PROJECT_ID" --name="$PROJECT_NAME"
gcloud config set project "$PROJECT_ID"
```

Windows PowerShell:

```powershell
gcloud projects create $env:PROJECT_ID --name="$env:PROJECT_NAME"
gcloud config set project $env:PROJECT_ID
```

If the project already exists, just select it:

```bash
gcloud config set project "$PROJECT_ID"
```

### Enable Billing

Billing is enabled on a project only when the project is linked to an active Cloud Billing account. Creating a project with `gcloud projects create` does not necessarily link billing automatically.

List the billing accounts your current Google account can access:

```bash
gcloud billing accounts list
```

The output contains billing account IDs in this format:

```text
XXXXXX-XXXXXX-XXXXXX
```

If the list is empty, the signed-in account does not have access to a billing account. Go back to the Console billing setup above, or ask the company billing administrator to create a billing account and grant you permission to link projects to it.

Link the project to the billing account:

```bash
gcloud billing projects link "$PROJECT_ID" --billing-account="BILLING_ACCOUNT_ID"
```

Windows PowerShell:

```powershell
gcloud billing projects link $env:PROJECT_ID --billing-account="BILLING_ACCOUNT_ID"
```

Verify that billing is enabled:

```bash
gcloud billing projects describe "$PROJECT_ID"
```

Windows PowerShell:

```powershell
gcloud billing projects describe $env:PROJECT_ID
```

Look for `billingEnabled: true`. If billing is not enabled, Cloud Run, Cloud Build, Artifact Registry, and Scheduler may not work correctly.

You can also verify billing in the Console:

1. Open https://console.cloud.google.com/billing
2. Select the project.
3. Confirm that it is linked to the intended Cloud Billing account.

### Expected Usage And Free-Tier Context

Billing must be enabled, but this project is designed for small scheduled sync jobs and low data volume. With typical dealership inventory sizes, it should remain far below the usual free-tier and API quota limits.

Real usage example:

- About 20 vehicles recorded.
- Generated Google Sheets file size: roughly 25-50 KB.
- One scheduled sync run usually performs a small number of Secret Manager reads, AG API requests, Google Sheets reads/writes, and Cloud Run execution seconds.

Current Google Cloud limits to keep in mind:

| Service | Current free-tier or quota detail | Why this project should stay low-volume |
| --- | --- | --- |
| Cloud Run Jobs | Monthly free tier includes 240,000 vCPU-seconds and 450,000 GiB-seconds, aggregated by billing account. | A scheduled Python sync job should normally run for seconds or minutes, not continuously. |
| Cloud Scheduler | 3 scheduler jobs are free per billing account; executions themselves are not billed separately. | This deployment needs one scheduler job. |
| Secret Manager | Free tier includes 6 active secret versions and 10,000 access operations per month. | This project uses 5 secrets and reads them only when the job runs. |
| Google Sheets API | Standard use is available at no additional cost; common quota limits include 300 read and 300 write requests per minute per project. | A small vehicle inventory produces a small number of sheet operations. |
| Cloud Storage | Small storage and operation volumes are usually inexpensive; check current pricing for production. | The JSON export is a small inventory snapshot rewritten only when the inventory changes. |
| Cloud Build | Google lists 2,500 free build-minutes per month for the default `e2-standard-2` pool, subject to change. | Builds happen only when deploying a new image, not on every scheduled run. |
| Artifact Registry | First 0.5 GB of storage is free; data transfer into Google Cloud and within the same location is generally free. | The container image and sheet data are small. |

Important caveats:

- Free tiers are usually calculated per billing account, not only per project.
- Some free tiers are region-dependent or applied as discounts based on specific regional pricing.
- Outbound internet data transfer can be billed depending on source, destination, and volume.
- Pricing and quotas can change, so check the official pages during handover.

For this project, the main operational cost control is keeping the schedule reasonable, for example once per day or a few times per day, unless the business explicitly needs more frequent updates.

### Create A 10 EUR Budget Alert

Create a budget before deploying the scheduled job. This does not create a hard spending cap, but it sends email alerts when the project reaches the configured thresholds. Google Cloud charges can be reported with some delay, so do not treat the budget as an automatic shutdown mechanism.

Recommended budget:

| Setting | Value |
| --- | --- |
| Budget amount | `10 EUR` |
| Budget period | Monthly |
| Scope | This project only |
| Alert thresholds | 50%, 80%, 100% |
| Trigger type | Actual spend |

Enable the Billing Budgets API:

```bash
gcloud services enable billingbudgets.googleapis.com
```

Windows PowerShell:

```powershell
gcloud services enable billingbudgets.googleapis.com
```

Find the billing account ID:

```bash
gcloud billing accounts list
```

The billing account ID has this format:

```text
XXXXXX-XXXXXX-XXXXXX
```

Set it as a variable.

Linux/macOS:

```bash
export BILLING_ACCOUNT_ID="XXXXXX-XXXXXX-XXXXXX"
```

Windows PowerShell:

```powershell
$env:BILLING_ACCOUNT_ID = "XXXXXX-XXXXXX-XXXXXX"
```

Create the budget with alerts at 50%, 80%, and 100% of actual spend.

Linux/macOS:

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

Windows PowerShell:

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

Verify the budget:

```bash
gcloud billing budgets list --billing-account="$BILLING_ACCOUNT_ID"
```

Windows PowerShell:

```powershell
gcloud billing budgets list --billing-account=$env:BILLING_ACCOUNT_ID
```

By default, Google Cloud sends budget alert emails to billing account IAM recipients. Do not use `--disable-default-iam-recipients` unless another notification channel is configured.

If the currency of the billing account is not EUR, `--budget-amount=10EUR` can fail. Use the billing account currency instead, for example `--budget-amount=10USD`, or the local-currency equivalent of 10 EUR.

Permissions needed:

- To create a budget on the Cloud Billing account, the user usually needs Billing Account Administrator or Billing Account Costs Manager access.
- If the user only has project-level access, they may still be able to create a budget scoped to projects they own, depending on project permissions.

Official documentation: https://cloud.google.com/billing/docs/how-to/budgets

## 5. Enable Required APIs

Enable the Google Cloud APIs used by the deployment.

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com \
  billingbudgets.googleapis.com \
  sheets.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com
```

Windows PowerShell:

```powershell
gcloud services enable `
  run.googleapis.com `
  artifactregistry.googleapis.com `
  cloudbuild.googleapis.com `
  cloudscheduler.googleapis.com `
  secretmanager.googleapis.com `
  storage.googleapis.com `
  billingbudgets.googleapis.com `
  sheets.googleapis.com `
  iam.googleapis.com `
  cloudresourcemanager.googleapis.com
```

Create the Google Cloud Storage bucket used for the JSON export. Bucket names are globally unique, so choose a production-specific name.

Linux/macOS:

```bash
gcloud storage buckets create "gs://$GCS_BUCKET_NAME" \
  --location="$REGION" \
  --uniform-bucket-level-access
```

Windows PowerShell:

```powershell
gcloud storage buckets create "gs://$env:GCS_BUCKET_NAME" `
  --location="$env:REGION" `
  --uniform-bucket-level-access
```

## 6. Create Service Accounts

Create one service account for the Cloud Run Job runtime and one service account for Cloud Scheduler.

Linux/macOS:

```bash
gcloud iam service-accounts create "$RUNTIME_SA_NAME" \
  --display-name="AG to Sheets runtime"

gcloud iam service-accounts create "$SCHEDULER_SA_NAME" \
  --display-name="AG to Sheets scheduler"

export PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
export RUNTIME_SA_EMAIL="$RUNTIME_SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
export SCHEDULER_SA_EMAIL="$SCHEDULER_SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
```

Windows PowerShell:

```powershell
gcloud iam service-accounts create $env:RUNTIME_SA_NAME `
  --display-name="AG to Sheets runtime"

gcloud iam service-accounts create $env:SCHEDULER_SA_NAME `
  --display-name="AG to Sheets scheduler"

$env:PROJECT_NUMBER = gcloud projects describe $env:PROJECT_ID --format="value(projectNumber)"
$env:RUNTIME_SA_EMAIL = "$env:RUNTIME_SA_NAME@$env:PROJECT_ID.iam.gserviceaccount.com"
$env:SCHEDULER_SA_EMAIL = "$env:SCHEDULER_SA_NAME@$env:PROJECT_ID.iam.gserviceaccount.com"
```

Grant the runtime service account permission to read secrets:

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

Windows PowerShell:

```powershell
gcloud projects add-iam-policy-binding $env:PROJECT_ID `
  --member="serviceAccount:$env:RUNTIME_SA_EMAIL" `
  --role="roles/secretmanager.secretAccessor"
```

Grant the runtime service account permission to rewrite the JSON object in the bucket:

```bash
gcloud storage buckets add-iam-policy-binding "gs://$GCS_BUCKET_NAME" \
  --member="serviceAccount:$RUNTIME_SA_EMAIL" \
  --role="roles/storage.objectUser"
```

Windows PowerShell:

```powershell
gcloud storage buckets add-iam-policy-binding "gs://$env:GCS_BUCKET_NAME" `
  --member="serviceAccount:$env:RUNTIME_SA_EMAIL" `
  --role="roles/storage.objectUser"
```

Share the target Google Sheet with the runtime service account email and give it Editor permission:

```text
ag-to-sheets-runner@PROJECT_ID.iam.gserviceaccount.com
```

This spreadsheet sharing step is required because Google Sheets document permissions are not controlled only by Google Cloud IAM.

## 7. Create Secret Manager Secrets

Create the required secrets.

Linux/macOS:

```bash
printf "%s" "https://your-ag-api-base-url" | gcloud secrets create AG_API_URL --data-file=-
printf "%s" "your-consumer-key" | gcloud secrets create AG_API_CONSUMER_KEY --data-file=-
printf "%s" "your-consumer-secret" | gcloud secrets create AG_API_CONSUMER_SECRET --data-file=-
printf "%s" "your-google-sheet-id" | gcloud secrets create SHEET_ID --data-file=-
printf "%s" "$GCS_BUCKET_NAME" | gcloud secrets create GCS_BUCKET_NAME --data-file=-
```

Windows PowerShell:

```powershell
"https://your-ag-api-base-url" | gcloud secrets create AG_API_URL --data-file=-
"your-consumer-key" | gcloud secrets create AG_API_CONSUMER_KEY --data-file=-
"your-consumer-secret" | gcloud secrets create AG_API_CONSUMER_SECRET --data-file=-
"your-google-sheet-id" | gcloud secrets create SHEET_ID --data-file=-
$env:GCS_BUCKET_NAME | gcloud secrets create GCS_BUCKET_NAME --data-file=-
```

To update an existing secret later, add a new version:

```bash
printf "%s" "new-value" | gcloud secrets versions add SECRET_ID --data-file=-
```

Windows PowerShell:

```powershell
"new-value" | gcloud secrets versions add SECRET_ID --data-file=-
```

## 8. Build And Push The Container Image With Google Cloud Build

Use Google Cloud Build for the standard deployment. This keeps the deployment independent from the local machine and avoids requiring Docker to be installed locally.

Create an Artifact Registry Docker repository:

```bash
gcloud artifacts repositories create "$REPOSITORY" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Container images for AG to Sheets sync"
```

Windows PowerShell:

```powershell
gcloud artifacts repositories create $env:REPOSITORY `
  --repository-format=docker `
  --location=$env:REGION `
  --description="Container images for AG to Sheets sync"
```

Build and push the image using Cloud Build:

Linux/macOS:

```bash
export IMAGE_URI="gcr.io/$PROJECT_ID/$JOB_NAME"
gcloud builds submit --tag "$IMAGE_URI"
```

Windows PowerShell:

```powershell
$env:IMAGE_URI = "gcr.io/$env:PROJECT_ID/$env:JOB_NAME"
gcloud builds submit --tag $env:IMAGE_URI
```

Optional local Docker build:

Use this only if you specifically want to build the image on your own machine, test the container locally, or deploy outside Google Cloud. For the normal Cloud Run Job deployment, use the Cloud Build commands above.

```bash
docker build -t "$IMAGE_URI" .
gcloud auth configure-docker "$REGION-docker.pkg.dev"
docker push "$IMAGE_URI"
```

## 9. Deploy The Cloud Run Job

Create the Cloud Run Job with the runtime service account.

Linux/macOS:

```bash
gcloud run jobs create "$JOB_NAME" \
  --image="$IMAGE_URI" \
  --region="$REGION" \
  --service-account="$RUNTIME_SA_EMAIL" \
  --tasks=1 \
  --max-retries=1 \
  --task-timeout=30m
```

Windows PowerShell:

```powershell
gcloud run jobs create $env:JOB_NAME `
  --image=$env:IMAGE_URI `
  --region=$env:REGION `
  --service-account=$env:RUNTIME_SA_EMAIL `
  --tasks=1 `
  --max-retries=1 `
  --task-timeout=30m
```

For later deployments, update the existing job:

```bash
gcloud run jobs update "$JOB_NAME" \
  --image="$IMAGE_URI" \
  --region="$REGION" \
  --service-account="$RUNTIME_SA_EMAIL"
```

Test the job manually:

```bash
gcloud run jobs execute "$JOB_NAME" --region="$REGION" --wait
```

Check which service account the job uses:

```bash
gcloud run jobs describe "$JOB_NAME" \
  --region="$REGION" \
  --format="value(template.template.serviceAccount)"
```

Read logs:

```bash
gcloud logging read \
  "resource.type=\"cloud_run_job\" AND resource.labels.job_name=\"$JOB_NAME\"" \
  --limit=50 \
  --format="value(textPayload)"
```

## 10. Configure Cloud Scheduler

Cloud Scheduler will call the Cloud Run Jobs API endpoint that executes the job.

Grant the scheduler service account permission to run Cloud Run jobs:

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SCHEDULER_SA_EMAIL" \
  --role="roles/run.invoker"
```

Windows PowerShell:

```powershell
gcloud projects add-iam-policy-binding $env:PROJECT_ID `
  --member="serviceAccount:$env:SCHEDULER_SA_EMAIL" `
  --role="roles/run.invoker"
```

Create the scheduler job. This example runs every day at 06:00 Europe/Paris time.

Linux/macOS:

```bash
gcloud scheduler jobs create http "$SCHEDULER_JOB_NAME" \
  --location="$REGION" \
  --schedule="0 6 * * *" \
  --time-zone="Europe/Paris" \
  --uri="https://run.googleapis.com/v2/projects/$PROJECT_ID/locations/$REGION/jobs/$JOB_NAME:run" \
  --http-method=POST \
  --oauth-service-account-email="$SCHEDULER_SA_EMAIL"
```

Windows PowerShell:

```powershell
gcloud scheduler jobs create http $env:SCHEDULER_JOB_NAME `
  --location=$env:REGION `
  --schedule="0 6 * * *" `
  --time-zone="Europe/Paris" `
  --uri="https://run.googleapis.com/v2/projects/${env:PROJECT_ID}/locations/${env:REGION}/jobs/${env:JOB_NAME}:run" `
  --http-method=POST `
  --oauth-service-account-email=$env:SCHEDULER_SA_EMAIL
```

Trigger the schedule manually:

```bash
gcloud scheduler jobs run "$SCHEDULER_JOB_NAME" --location="$REGION"
```

Windows PowerShell:

```powershell
gcloud scheduler jobs run $env:SCHEDULER_JOB_NAME --location=$env:REGION
```

## 11. Operational Checks

After deployment, verify the full chain:

1. Cloud Scheduler exists and has the expected schedule.
2. Cloud Scheduler can trigger the Cloud Run Job.
3. The Cloud Run Job uses the dedicated runtime service account.
4. The runtime service account has `roles/secretmanager.secretAccessor`.
5. The runtime service account has Editor access to the Google Sheet.
6. The runtime service account has `roles/storage.objectUser` on the JSON export bucket.
7. Secret Manager contains these secrets:
   - `AG_API_URL`
   - `AG_API_CONSUMER_KEY`
   - `AG_API_CONSUMER_SECRET`
   - `SHEET_ID`
   - `GCS_BUCKET_NAME`
8. The Google Sheet is either completely empty before the first run or already initialized by a previous successful pipeline run.
9. A manual job execution finishes successfully and creates or rewrites `vehicles.json` in the configured bucket.

Useful commands:

```bash
gcloud scheduler jobs describe "$SCHEDULER_JOB_NAME" --location="$REGION"
gcloud run jobs describe "$JOB_NAME" --region="$REGION"
gcloud secrets list
gcloud storage ls "gs://$GCS_BUCKET_NAME"
gcloud run jobs executions list --job="$JOB_NAME" --region="$REGION"
```

## 12. Common Problems

### Permission denied when reading secrets

The runtime service account is missing Secret Manager access.

Fix:

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

### Permission denied when editing Google Sheets

The Google Sheet was not shared with the runtime service account.

Fix:

1. Open the Google Sheet.
2. Click Share.
3. Add the runtime service account email.
4. Grant Editor permission.

### Scheduler cannot trigger the job

The scheduler service account is missing permission to invoke Cloud Run jobs.

Fix:

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SCHEDULER_SA_EMAIL" \
  --role="roles/run.invoker"
```

### Wrong Google Cloud project is used

Check the current project:

```bash
gcloud config get-value project
```

Set it explicitly:

```bash
gcloud config set project "$PROJECT_ID"
```

The application itself resolves the project ID from default Google auth or from `GOOGLE_CLOUD_PROJECT`.

## References

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
