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

The Swift service boundary translates the successful result or error code into application state; page code never receives transport details.

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

Every deployment creates paid-capable remote state and requires an exact resource review and explicit approval. The service-local `.gcloudignore` excludes tests, development dependencies, environment files, caches, and documentation from source upload. The project inherits domain-restricted sharing, so public invocation uses the service-level `--no-invoker-iam-check` setting rather than a prohibited `allUsers` binding.

### One-Time Project Setup

The retained development project is `silent-window-507419-e1` in `europe-west2`. Its APIs and Google-created source-build identity are already configured; these commands are setup and recovery references, not routine deployment steps:

```text
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project silent-window-507419-e1

gcloud projects add-iam-policy-binding silent-window-507419-e1 --member='serviceAccount:334553986819-compute@developer.gserviceaccount.com' --role='roles/run.builder' --condition=None
```

### Retained Development Deployment

Before an approved deployment, record the source revision and whether the service boundary is dirty:

```text
git rev-parse --short=12 HEAD
git status --short -- app/services/work-on-the-decayed
```

Deploy the filtered service source with the accepted resource bounds:

```text
gcloud run deploy work-on-the-decayed --project silent-window-507419-e1 --region europe-west2 --source app/services/work-on-the-decayed --no-invoker-iam-check --ingress all --cpu 1 --memory 512Mi --cpu-throttling --concurrency 8 --min-instances 0 --max-instances 1 --timeout 10s --port 8080 --description 'Dotlineform App development rotation service'
```

Source deployment remains the deliberate workflow while there is one development environment. It uploads the filtered source, runs the retained Dockerfile once in Cloud Build, stores an immutable image in Artifact Registry, and deploys a Cloud Run revision resolved to that image digest. Introduce a separate build-once/promote-by-digest path only when a second environment, repeat deployment of one exact artifact, or a stronger rollback requirement creates an actual promotion boundary.

### Evidence And Smoke

After deployment, retrieve the endpoint and latest revision without storing credentials in the repository:

```text
SERVICE_URL="$(gcloud run services describe work-on-the-decayed --project silent-window-507419-e1 --region europe-west2 --format 'value(status.url)')"
REVISION="$(gcloud run services describe work-on-the-decayed --project silent-window-507419-e1 --region europe-west2 --format 'value(status.latestReadyRevisionName)')"
gcloud run revisions describe "$REVISION" --project silent-window-507419-e1 --region europe-west2 --format 'value(status.imageDigest)'
gcloud builds list --project silent-window-507419-e1 --region europe-west2 --filter 'tags=service_work-on-the-decayed' --sort-by '~createTime' --limit 1 --format 'table(id,status,createTime,results.images[0].digest)'
```

Run only the two narrow deployed contract smokes:

```text
curl --fail-with-body --silent --show-error --header 'Content-Type: application/json' --data '{"action":"rotate-symbol"}' "$SERVICE_URL/v1/rotate-symbol"
curl --include --silent --show-error --header 'Content-Type: application/json' --data '{"action":"wrong"}' "$SERVICE_URL/v1/rotate-symbol"
```

Accept only HTTP 200 with `{"quarterTurns":1}` and HTTP 400 with `{"error":{"code":"invalid-request"}}`. Record the Git state, Cloud Build ID and status, Cloud Run revision, immutable image digest, and both smoke outcomes.

### Artifact Retention

Retain the source archive and image digest for the serving revision and the immediately preceding accepted rollback revision. Before deleting anything, list Cloud Run revisions and their image digests, source archives, and Artifact Registry versions; delete only explicitly identified artifacts that are not referenced by either retained revision. Do not delete by the moving `latest` tag alone.

No automatic cleanup policy is justified while the repository holds fewer than five image versions and remains below 250 MB. Review cleanup when either threshold is crossed. The initial state is one serving revision, one 48.9 MB image, and two source archives totalling about 6 KiB; the extra archive is from the stopped first deployment attempt and is harmless. Cleanup is a separately reviewed destructive operation, never part of deployment or smoke testing.
