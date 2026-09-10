# ProofStack Requirements

## Product statement

ProofStack is a personal evidence application. It lets one fixed demo user upload a file, save descriptive metadata, browse evidence, open a record, download its file through a temporary URL, and delete the evidence and file.

## Architecture constraints

1. The frontend shall use React, Vite, and TypeScript.
2. The backend shall use five standalone Python Lambda handlers behind an API Gateway REST API with endpoint type Regional, Lambda proxy integration, and named stage `prod`.
3. Metadata shall be stored in DynamoDB with string keys named `PK` and `SK`.
4. Evidence files shall be stored in a private S3 bucket with Block Public Access enabled. The built frontend shall be hosted in a separate public S3 bucket.
5. Every data operation shall use `USER#demo`; ProofStack shall not implement authentication or user registration.
6. AWS resources shall be provisioned and configured only through the AWS Management Console.
7. Each Lambda file shall be independently copyable into the Lambda Console as `lambda_function.py` and shall not depend on project-local runtime modules.

## REST API configuration

1. The final REST resource tree shall contain `/uploads/presign`, `/evidence`, and `/evidence/{id}`.
2. The final business methods shall be `POST /uploads/presign`, `POST /evidence`, `GET /evidence`, `GET /evidence/{id}`, and `DELETE /evidence/{id}`. Every business method shall use Lambda proxy integration.
3. Every business method and `OPTIONS` method shall use **Authorization** `NONE` and **API Key Required** false.
4. Each final callable resource shall have an `OPTIONS` method with a `MOCK` integration. Initially it shall return `Access-Control-Allow-Origin: http://localhost:5173`, `Access-Control-Allow-Headers: content-type,accept`, and these exact `Access-Control-Allow-Methods` values:
   - `/uploads/presign`: `POST,OPTIONS`
   - `/evidence`: `GET,POST,OPTIONS`
   - `/evidence/{id}`: `GET,DELETE,OPTIONS`
5. Gateway Responses `DEFAULT_4XX` and `DEFAULT_5XX` shall include the local-origin CORS headers so gateway-generated errors are browser-readable.
6. REST proxy events shall use top-level `httpMethod`, `path`, and `resource`; parameterized requests shall use `pathParameters.id`; Lambda Console events shall set `requestContext.stage` to `prod`.
7. The API shall be explicitly deployed to `prod` after initial setup and redeployed after every resource, method, integration, CORS, or Gateway Response change. The frontend invoke base shall be `https://<api-id>.execute-api.<region>.amazonaws.com/prod`, without a trailing slash.
8. During phase 5, the exact website origin shall replace localhost in all REST `OPTIONS` responses, `DEFAULT_4XX`, `DEFAULT_5XX`, and all Lambda `ALLOWED_ORIGIN` values, after which `prod` shall be redeployed. Private evidence-bucket CORS may retain both localhost and the website origin.

### Incremental provisioning contract

The final API contract above remains stable even though the workshop provisions it incrementally.

- Phase 1 shall create only a disposable `/workshop` resource with `GET` and `OPTIONS` MOCK integrations, local CORS, Gateway Responses, and a `prod` deployment. The final service resources shall not be created yet.
- Phase 2 shall switch `GET /workshop` to Lambda proxy integration with the first Lambda, `proofstack-list-evidence`, while keeping its handler dependency-free, then redeploy and test it.
- Phase 3 shall create `/evidence` and `/evidence/{id}` with their final metadata methods and exact `OPTIONS` behavior. The temporary `/workshop` resource shall be removed before phase 3 is complete, followed by redeployment.
- Phase 4 shall add `/uploads/presign` only after the private evidence bucket and signed-upload handler are ready, configure its final method and `OPTIONS`, and redeploy.
- `/workshop` is a teaching scaffold only. It is not part of the final API and shall not coexist with the completed phase-3 API.

## API contract

All JSON errors shall use this envelope:

```json
{"error":{"code":"ERROR_CODE","message":"Safe message"}}
```

Successful responses shall be JSON except for the empty `204` delete response. The resource variable shall be named `id` and supplied as `pathParameters.id`.

### 1. Request an upload

- `POST /uploads/presign` shall accept JSON fields `fileName` and `contentType`.
- A successful response shall contain `uploadUrl`, `assetKey`, and `expiresIn`.
- `assetKey` shall be unique and start with `evidence/demo/`.
- The short-lived PUT URL shall target the private evidence bucket and bind the submitted content type.
- Invalid input shall return `400`; missing required configuration shall return `500` with code `CONFIGURATION_ERROR`; safe dependency failures shall return `500`.

### 2. Create evidence metadata

- `POST /evidence` shall accept valid metadata containing `assetKey` after the browser upload succeeds.
- The handler shall generate `id` as a compact UTC timestamp followed by a UUID segment, for example `20250102T030405123456Z-a1b2c3d4`.
- The item shall use `PK = USER#demo` and `SK = EVIDENCE#<id>` and include `id`, `title`, `description`, `assetKey`, `fileName`, `contentType`, and `createdAt`.
- The handler shall use `dynamodb:PutItem` only for application data access.
- A successful create shall return `201` with the created evidence record and shall not expose `PK` or `SK`.

### 3. List evidence

- `GET /evidence` shall use DynamoDB Query, never Scan, for `PK = USER#demo` and the `EVIDENCE#` sort-key prefix.
- The Query shall run in descending sort-key order so the timestamp-first IDs return newest records first.
- The response shall contain all matching `items`; ProofStack shall not implement pagination or return pagination tokens.
- The response shall not expose `PK` or `SK`.
- After signed downloads are enabled in phase 4, each returned record may include a short-lived `assetUrl` generated from its `assetKey`.

### 4. Get evidence

- `GET /evidence/{id}` shall read `pathParameters.id` and retrieve `PK = USER#demo`, `SK = EVIDENCE#<id>` with DynamoDB GetItem.
- A missing record shall return `404`.
- After signed downloads are enabled in phase 4, the returned record may include a short-lived `assetUrl` generated from `assetKey`.

### 5. Delete evidence

- `DELETE /evidence/{id}` shall read `pathParameters.id`, retrieve the item, and use its `assetKey`.
- The final handler shall delete the exact S3 object first and call DynamoDB DeleteItem only after S3 deletion succeeds. Metadata shall remain if S3 deletion fails.
- During phase 3, delete shall stop after metadata lookup and retain the item because private S3 deletion is not yet available.
- A missing record shall return `404`; a successful final delete shall return `204` with no body.

### 6. Frontend experience

- The frontend shall provide upload-and-create, list, detail/download, delete confirmation, loading, empty, success, validation, not-found, and dependency-failure states.
- The frontend shall centralize typed API requests and use `assetKey`; it may consume temporary `assetUrl` values but shall not persist or log them.
- The frontend shall read its `/prod` API invoke base from `VITE_API_BASE_URL` and shall not contain AWS credentials or private bucket details.

## Configuration requirements

Lambda deployment values shall use only these names: `TABLE_NAME`, `ASSET_BUCKET`, `ALLOWED_ORIGIN`, `UPLOAD_URL_EXPIRY_SECONDS`, and `DOWNLOAD_URL_EXPIRY_SECONDS`.

- `ALLOWED_ORIGIN`: set to `http://localhost:5173` as each handler is introduced, then replaced on all five handlers with the deployed website origin in phase 5.
- `TABLE_NAME`: list, create, get, and delete beginning in phase 3.
- `ASSET_BUCKET`: presign, list, get, and delete beginning in phase 4.
- `UPLOAD_URL_EXPIRY_SECONDS`: presign beginning in phase 4.
- `DOWNLOAD_URL_EXPIRY_SECONDS`: list and get beginning in phase 4.

Before a handler receives required resource configuration, it shall return a controlled `500 CONFIGURATION_ERROR`. When all configuration required for an operation is present but that operation is not yet implemented, it shall return `501 NOT_IMPLEMENTED`.

## Delivery and quality requirements

- Complete the phases in order: disposable API Gateway `/workshop` foundation; first dependency-free list Lambda behind `/workshop`; DynamoDB metadata API and removal of `/workshop`; private S3 signed upload/download and complete delete; React build and public S3 hosting with final origin cutover.
- Phase 2 shall create only `proofstack-list-evidence`. Phase 3 shall evolve it and create the create, get, and delete metadata Lambdas. Phase 4 shall create the presign Lambda, bringing the final total to five standalone handlers.
- Follow test-driven development with focused local tests for success, validation, not-found, configuration, and dependency-failure behavior.
- After every handler change, run the matching Lambda Console test with an API Gateway REST API Lambda proxy event for `prod`.
- Redeploy `prod` at every phase transition and after every API resource, method, integration, CORS, or Gateway Response change.
- Logs shall not contain file contents, internal keys, credentials, raw dependency errors, or presigned URLs.
- IAM permissions shall be exact least privilege: presign `s3:PutObject`; create `dynamodb:PutItem`; list `dynamodb:Query` and, after signed downloads are enabled, `s3:GetObject`; get `dynamodb:GetItem` and `s3:GetObject`; delete `dynamodb:GetItem`, then `s3:DeleteObject`, then `dynamodb:DeleteItem`. DynamoDB access shall target the exact table ARN and S3 access the exact `evidence/demo/*` object ARN.
