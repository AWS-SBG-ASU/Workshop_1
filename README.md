# ProofStack

ProofStack is a personal evidence application for one fixed demo user. It uploads private files, stores descriptive metadata, lists and retrieves records, provides short-lived download links, and deletes records with their files.

## Architecture

```text
React + Vite + TypeScript (public S3 website)
             |
             v
API Gateway HTTP API (payload format 2.0)
             |
             v
Five standalone Python Lambda functions
       |                 |
       v                 v
DynamoDB            private S3 bucket
PK / SK metadata    signed PUT and GET
```

Every data operation uses `PK = USER#demo`. Evidence files use the private prefix `evidence/demo/`. The browser never receives AWS credentials, and public access is enabled only for the separate frontend bucket.

| Route                   | Purpose                                                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------------------------- |
| `POST /uploads/presign` | Accept `fileName` and `contentType`; return `uploadUrl`, `assetKey`, and `expiresIn`.                     |
| `POST /evidence`        | Save metadata containing `assetKey` after upload.                                                         |
| `GET /evidence`         | Query records newest first with no pagination; phase 4 responses may include temporary `assetUrl` values. |
| `GET /evidence/{id}`    | Return one record; phase 4 responses may include a temporary `assetUrl`.                                  |
| `DELETE /evidence/{id}` | Delete the exact private asset, then delete its metadata.                                                 |

Parameterized events use `pathParameters.id`. API errors use `{"error":{"code":"...","message":"..."}}`; a successful delete returns an empty `204`.

## Repository layout

```text
frontend/           React, Vite, and TypeScript browser application
backend/functions/  standalone Python Lambda handlers
backend/events/     API Gateway HTTP API payload v2.0 events
backend/tests/      local handler tests
docs/               AWS setup, testing, troubleshooting, and cleanup
```

## Prerequisites

- An AWS account with permission to configure API Gateway, Lambda, DynamoDB, IAM, and S3 in `us-east-1`.
- Node.js 20.19 or later and npm.
- Python 3.11 or later and pip.
- A modern browser.

Do not store credentials, generated presigned URLs, resource names, or local environment values in version control.

## Local checks

Run these commands from the repository root:

```text
python -m pip install -r backend/requirements-dev.txt
python -m pytest -c backend/pytest.ini backend/tests
npm --prefix frontend install
npm --prefix frontend test
npm --prefix frontend run build
```

For local frontend development, copy `frontend/.env.example` to `frontend/.env.local`, set `VITE_API_BASE_URL` to the HTTP API invoke URL without a trailing slash, then run:

```text
npm --prefix frontend run dev
```

## Deployment order

Follow [AWS Console setup](docs/aws-console-setup.md) in this required order:

1. Create the API Gateway HTTP API shell and configure CORS for `http://localhost:5173`.
2. Create the five Lambdas, set `ALLOWED_ORIGIN`, and connect the five routes.
3. Create DynamoDB and activate metadata operations.
4. Create the private S3 bucket and activate signed PUT/GET and delete behavior.
5. Build React, deploy it to the separate public S3 bucket, add the website origin to CORS, and update `ALLOWED_ORIGIN`.

See [Lambda Console testing](docs/lambda-console-testing.md), [troubleshooting](docs/troubleshooting.md), and [cleanup](docs/cleanup.md) for operational guidance.