# ProofStack

ProofStack is a personal evidence application for one fixed demo user. It uploads private files, stores descriptive metadata, lists and retrieves records, provides short-lived download links, and deletes records with their files.

## Architecture

```text
React + Vite + TypeScript (public S3 website)
             |
             v
API Gateway Regional REST API (stage: prod)
             | Lambda proxy integration
             v
Five standalone Python Lambda functions
       |                 |
       v                 v
DynamoDB            private S3 bucket
PK / SK metadata    signed PUT and GET
```

Every data operation uses `PK = USER#demo`. Evidence files use the private prefix `evidence/demo/`. The browser never receives AWS credentials, and public access is enabled only for the separate frontend bucket.

| Route                   | Purpose                                                                                                           |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `POST /uploads/presign` | Accept `fileName` and `contentType`; return `uploadUrl`, `assetKey`, and `expiresIn`.                             |
| `POST /evidence`        | Save metadata containing `assetKey` after upload.                                                                 |
| `GET /evidence`         | Query records newest first with no pagination; signed-download responses may include temporary `assetUrl` values. |
| `GET /evidence/{id}`    | Return one record; signed-download responses may include a temporary `assetUrl`.                                  |
| `DELETE /evidence/{id}` | Delete the exact private asset, then delete its metadata.                                                         |

Business methods use Lambda proxy integration with **Authorization** `NONE` and **API Key Required** false. REST proxy events use top-level `httpMethod`, `path`, and `resource`; parameterized events use `pathParameters.id`; Console events set `requestContext.stage` to `prod`. API errors use `{"error":{"code":"...","message":"..."}}`; a successful delete returns an empty `204`.

Each REST resource has an `OPTIONS` MOCK method with local-development CORS and its exact method list. Gateway Responses `DEFAULT_4XX` and `DEFAULT_5XX` also include CORS. API changes are explicitly deployed to the named `prod` stage; the frontend base is `https://<api-id>.execute-api.<region>.amazonaws.com/prod`.

## Repository layout

```text
frontend/           React, Vite, and TypeScript browser application
backend/functions/  standalone Python Lambda handlers
backend/events/     Lambda Console request fixtures
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

For local frontend development, copy `frontend/.env.example` to `frontend/.env.local`, set `VITE_API_BASE_URL` to the REST API invoke base ending in `/prod` without a trailing slash, then run:

```text
npm --prefix frontend run dev
```

## Deployment order

Follow [AWS Console setup](docs/aws-console-setup.md) in this required order:

1. Create only a temporary `/workshop` resource on the Regional REST API with `GET` and `OPTIONS` MOCK integrations, local CORS and default Gateway Responses, then deploy `prod`.
2. Create only `proofstack-list-evidence` with a dependency-free workshop handler, switch `GET /workshop` to Lambda proxy, then redeploy and test.
3. Create `ProofStackEvidence`, evolve list, add create/get/delete metadata Lambdas and the `/evidence` resources and methods, keep delete incomplete so metadata remains, remove `/workshop`, then redeploy.
4. Create the private S3 bucket, add presign and enhanced list/get/delete behavior, only then add `/uploads/presign`, complete exact IAM and local lifecycle verification, then redeploy.
5. Build React, deploy it to the separate public S3 bucket, replace localhost in final REST/Lambda CORS, retain both origins in private S3 CORS, and redeploy `prod`.

The completed system has exactly the five stable business routes and five standalone Lambdas described above; `/workshop` is disposable teaching infrastructure and must be absent by the end of phase 3.

See [Lambda Console testing](docs/lambda-console-testing.md), [troubleshooting](docs/troubleshooting.md), and [cleanup](docs/cleanup.md) for operational guidance.
