# Work On The Decayed Service

This provider-neutral Python service proves the retained App cloud boundary. It accepts one finite operation and returns one quarter-turn result. It does not own application UI state, private content, persistent data, or cloud credentials.

## Contract

`POST /v1/rotate-symbol` requires `Content-Type: application/json` and the exact body:

```json
{"action":"rotate-symbol"}
```

A successful response is:

```json
{"quarterTurns":1}
```

Rejected requests return a bounded code without user-facing copy:

```json
{"error":{"code":"invalid-request"}}
```

The Swift service boundary will translate the successful result or error code into application state during SAF-1.4.

## Local Development

From the repository root, create the ignored App service environment and install its development dependencies:

```text
$HOME/miniconda3/bin/python3 -m venv var/app/python/work-on-the-decayed
var/app/python/work-on-the-decayed/bin/python -m pip install --requirement app/services/work-on-the-decayed/requirements-dev.txt
```

Run the focused tests:

```text
PYTHONPATH=app/services/work-on-the-decayed/src var/app/python/work-on-the-decayed/bin/python -m pytest app/services/work-on-the-decayed/tests
```

Run the complete local HTTP service:

```text
PORT=8080 PYTHONPATH=app/services/work-on-the-decayed/src var/app/python/work-on-the-decayed/bin/python -m gunicorn --bind 127.0.0.1:8080 --workers 1 --threads 8 --timeout 30 --access-logfile - --error-logfile - --no-control-socket 'work_on_the_decayed.http:create_app()'
```

Then exercise the contract:

```text
curl --fail-with-body --silent --show-error --header 'Content-Type: application/json' --data '{"action":"rotate-symbol"}' http://127.0.0.1:8080/v1/rotate-symbol
```

The existing repository Dev Container and Codex setup install `requirements-dev.txt` through the root `requirements.txt`; they do not use a second App-specific development image.

## Container Build

The production image contains only pinned runtime dependencies and service source. A local Docker runtime is optional:

```text
docker build --tag work-on-the-decayed:local app/services/work-on-the-decayed
```

Cloud Run injects `PORT`; the container listens on `0.0.0.0` at that value and runs as an unprivileged user.

## Deployment Gate

Do not run the following commands until the exact resource preview has been reviewed and deployment has been approved. The service-local `.gcloudignore` excludes tests, development dependencies, environment files, caches, and documentation from source upload. The first source deployment enables paid-capable APIs, runs Cloud Build, uploads the remaining source through Google-managed storage, creates the `cloud-run-source-deploy` Artifact Registry repository when absent, creates a Cloud Run service and immutable revision, and allows public unauthenticated invocation.

The project inherits domain-restricted sharing, which correctly prohibits an `allUsers` IAM binding. Cloud Run's recommended equivalent is to disable its service-level Invoker IAM check with `--no-invoker-iam-check`; the organization policy remains in force. Enabling the Cloud Run API creates the default compute service account used by source builds. Grant that exact identity only the required Cloud Run Builder role and allow a short period for the new binding to propagate before deployment.

The approved command shape is:

```text
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project silent-window-507419-e1

gcloud projects add-iam-policy-binding silent-window-507419-e1 --member='serviceAccount:334553986819-compute@developer.gserviceaccount.com' --role='roles/run.builder' --condition=None

gcloud run deploy work-on-the-decayed --project silent-window-507419-e1 --region europe-west2 --source app/services/work-on-the-decayed --no-invoker-iam-check --ingress all --cpu 1 --memory 512Mi --cpu-throttling --concurrency 8 --min-instances 0 --max-instances 1 --timeout 10s --port 8080 --description 'Dotlineform App development rotation service'
```

After deployment, retrieve the assigned HTTPS endpoint without storing credentials in the repository:

```text
gcloud run services describe work-on-the-decayed --project silent-window-507419-e1 --region europe-west2 --format 'value(status.url)'
```

Use that returned URL for narrow valid-request and invalid-request deployed contract smokes. The native application is not connected until SAF-1.4.
