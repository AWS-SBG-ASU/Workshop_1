# ProofStack Design

## System overview

A React/Vite/TypeScript single-page application calls an API Gateway Regional REST API through its named `prod` stage. Five standalone Python Lambdas use Lambda proxy integration, a DynamoDB metadata table, and a private S3 evidence bucket. A separate public S3 bucket hosts the frontend build.

```text
Browser -> API Gateway Regional REST API /prod -> five Python Lambdas
                                                   |-> DynamoDB metadata table
                                                   `-> private evidence S3 bucket
Browser -> public frontend S3 bucket
```

Every data operation uses `USER#demo`. The private bucket keeps Block Public Access enabled; only built frontend assets in the separate website bucket are public.

## Components

| Component                | Responsibility                                                                                                             |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `presign_upload` Lambda  | Validate `fileName` and `contentType`; return `uploadUrl`, `assetKey`, and `expiresIn`.                                    |
| `create_evidence` Lambda | Validate metadata, generate a sortable ID, and put one DynamoDB item.                                                      |
| `list_evidence` Lambda   | Query the fixed partition newest first with no pagination; optionally add temporary `assetUrl` values after S3 is enabled. |
| `get_evidence` Lambda    | Get one item; optionally add a temporary `assetUrl` after S3 is enabled.                                                   |
| `delete_evidence` Lambda | Get metadata, delete its exact S3 asset, then delete the DynamoDB item.                                                    |
| React frontend           | Coordinate signed upload, metadata create, list, view/download, and confirmed delete.                                      |

Each Lambda source is self-contained, exports `lambda_handler`, uses only the Python standard library and the Lambda-provided AWS SDK, and is directly copyable to `lambda_function.py`.

## REST API contract

| Resource           | Business methods | Lambda target(s)                   | `OPTIONS` allow methods |
| ------------------ | ---------------- | ---------------------------------- | ----------------------- |
| `/uploads/presign` | `POST`           | `presign_upload`                   | `POST,OPTIONS`          |
| `/evidence`        | `POST`, `GET`    | `create_evidence`, `list_evidence` | `GET,POST,OPTIONS`      |
| `/evidence/{id}`   | `GET`, `DELETE`  | `get_evidence`, `delete_evidence`  | `GET,DELETE,OPTIONS`    |

Every business method uses Lambda proxy integration. Every business method and `OPTIONS` method sets **Authorization** to `NONE` and **API Key Required** to false. The API endpoint type is Regional.

| Route                   | Success | Main errors                                         |
| ----------------------- | ------: | --------------------------------------------------- |
| `POST /uploads/presign` |   `200` | `400`, `500`, `501` during incomplete phases        |
| `POST /evidence`        |   `201` | `400`, `500`, `501` during incomplete phases        |
| `GET /evidence`         |   `200` | `500`, `501` during incomplete phases               |
| `GET /evidence/{id}`    |   `200` | `400`, `404`, `500`, `501` during incomplete phases |
| `DELETE /evidence/{id}` |   `204` | `400`, `404`, `500`, `501` during incomplete phases |

REST proxy events carry top-level `httpMethod`, `path`, and `resource`; item requests use `pathParameters.id`; Console test events include `requestContext.stage = "prod"`. Request bodies are JSON strings. JSON errors always use:

```json
{"error":{"code":"NOT_FOUND","message":"Evidence was not found."}}
```

A missing required environment variable produces `500` with code `CONFIGURATION_ERROR`. If all required configuration is present but the requested operation is unfinished, the handler produces `501` with code `NOT_IMPLEMENTED`. Raw dependency errors never reach responses.

Presign request:

```json
{"fileName":"receipt.pdf","contentType":"application/pdf"}
```

Presign success:

```json
{"uploadUrl":"temporary signed URL","assetKey":"evidence/demo/unique-receipt.pdf","expiresIn":900}
```

Evidence records use `assetKey`. After signed downloads are enabled, list and get responses may add `assetUrl`; temporary URLs are never stored in DynamoDB or logged.

## CORS and deployment design

Each final resource has an `OPTIONS` method with a `MOCK` integration. Initially, method and integration responses expose `Access-Control-Allow-Origin: http://localhost:5173`, `Access-Control-Allow-Headers: content-type,accept`, and the exact allow-method value from the resource table. Gateway Responses `DEFAULT_4XX` and `DEFAULT_5XX` expose the same local origin and headers, with `GET,POST,DELETE,OPTIONS`, so gateway-generated failures are readable by the browser. Lambda responses also use `ALLOWED_ORIGIN`.

The REST API is explicitly deployed to the named stage `prod`; its frontend base is `https://<api-id>.execute-api.<region>.amazonaws.com/prod`. Any resource, method, integration, `OPTIONS`, or Gateway Response change requires an explicit redeployment to `prod`.

Phase 1 uses the same local-origin pattern on the disposable `/workshop` resource with `GET,OPTIONS`. That resource is removed before phase 3 completes and is not part of the final API. In phase 5, the exact S3 website origin replaces localhost in all final REST `OPTIONS` responses, both default Gateway Responses, and all Lambda `ALLOWED_ORIGIN` values, followed by a `prod` redeployment. The private evidence bucket CORS rule retains both localhost and the website origin for direct signed `PUT`, `GET`, and `HEAD` requests.

## Data model

DynamoDB keys are strings:

- `PK`: `USER#demo`
- `SK`: `EVIDENCE#<id>`

The `id` format is a compact, fixed-width UTC timestamp followed by a UUID segment, such as `20250102T030405123456Z-a1b2c3d4`. Timestamp-first IDs make lexicographic sort-key order chronological while the UUID segment keeps IDs unique.

Evidence attributes:

- `id`: compact UTC timestamp plus UUID segment
- `title`: required display title
- `description`: optional text
- `assetKey`: private S3 key under `evidence/demo/`
- `fileName`: original display name
- `contentType`: validated MIME type
- `createdAt`: UTC ISO 8601 timestamp

List uses DynamoDB Query with `PK = USER#demo`, an `EVIDENCE#` sort-key prefix, and descending sort-key order. It never uses Scan and has no pagination. API responses omit `PK` and `SK`.

## File and record flow

1. The frontend sends `fileName` and `contentType` to the presign resource.
2. Presign generates a unique `assetKey` under `evidence/demo/` and returns a short-lived PUT URL.
3. The browser uploads directly to the private bucket with the signed content type.
4. After a successful upload, the frontend creates metadata containing that `assetKey`.
5. After private S3 is enabled, list and get may generate short-lived GET URLs as `assetUrl` values.
6. Delete gets the metadata, deletes the exact object identified by `assetKey`, and then deletes the item. If S3 deletion fails, the item remains for retry.

## Configuration

| Handler | Required environment variables                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------- |
| Presign | `ALLOWED_ORIGIN`; with private S3: `ASSET_BUCKET`, `UPLOAD_URL_EXPIRY_SECONDS`                                |
| Create  | `ALLOWED_ORIGIN`; with DynamoDB: `TABLE_NAME`                                                                 |
| List    | `ALLOWED_ORIGIN`; with DynamoDB: `TABLE_NAME`; with private S3: `ASSET_BUCKET`, `DOWNLOAD_URL_EXPIRY_SECONDS` |
| Get     | `ALLOWED_ORIGIN`; with DynamoDB: `TABLE_NAME`; with private S3: `ASSET_BUCKET`, `DOWNLOAD_URL_EXPIRY_SECONDS` |
| Delete  | `ALLOWED_ORIGIN`; with DynamoDB: `TABLE_NAME`; with private S3: `ASSET_BUCKET`                                |

Set `ALLOWED_ORIGIN=http://localhost:5173` as each Lambda is introduced. Replace it on all five handlers with the exact public website origin in phase 5. Expiry values are short positive durations such as 900 seconds.

## Least-privilege IAM

| Handler | DynamoDB                                  | Private S3        |
| ------- | ----------------------------------------- | ----------------- |
| Presign | none                                      | `s3:PutObject`    |
| Create  | `dynamodb:PutItem`                        | none              |
| List    | `dynamodb:Query`                          | `s3:GetObject`    |
| Get     | `dynamodb:GetItem`                        | `s3:GetObject`    |
| Delete  | `dynamodb:GetItem`, `dynamodb:DeleteItem` | `s3:DeleteObject` |

DynamoDB permissions target the exact table ARN. S3 permissions target `arn:aws:s3:::<asset-bucket>/evidence/demo/*`. Phase 3 grants delete only `dynamodb:GetItem`; `dynamodb:DeleteItem` is added in phase 4 when S3-first deletion can be enforced.

## Learning progression

1. **API Gateway foundation:** create only temporary `GET` and `OPTIONS` MOCK methods on `/workshop`, configure local CORS and default Gateway Responses, and deploy the Regional REST API to `prod`. This isolates resource, method, CORS, and deployment concepts before compute is introduced.
2. **First Lambda:** create only `proofstack-list-evidence` with a dependency-free `GET /workshop` handler, switch the existing GET integration from MOCK to Lambda proxy, redeploy, and test. This demonstrates the API-to-Lambda transition without data-service complexity.
3. **DynamoDB metadata:** create `ProofStackEvidence`, evolve list, and add create/get/delete metadata Lambdas. Add `/evidence` and `/evidence/{id}` with final metadata methods and exact `OPTIONS`, grant exact DynamoDB IAM, keep delete intentionally incomplete so metadata remains, remove `/workshop`, and redeploy. This introduces persistence before file storage.
4. **Private S3 lifecycle:** create the private evidence bucket, add the fifth presign Lambda, enhance list/get/delete, grant exact S3 IAM plus delete's `dynamodb:DeleteItem`, and only now add `/uploads/presign` with its exact `OPTIONS`. Redeploy and verify the full local S3-first lifecycle.
5. **Public frontend:** build React, publish only its built assets to a separate public S3 bucket, replace localhost in final API and Lambda CORS with the website origin, retain both allowed private-S3 origins, redeploy `prod`, and verify all five final routes.

The temporary `/workshop` route is disposable teaching infrastructure. It must be absent by the end of phase 3 and does not alter the final system overview or API contract.

## Frontend and verification

Keep API types and requests in one typed client. Presentation components do not coordinate multi-step upload/create behavior. Read the `/prod` API invoke base from `VITE_API_BASE_URL`; never embed AWS credentials or private resource names.

Use test-driven development. Local Lambda tests use REST API Lambda proxy events for `prod` and replace AWS SDK clients with deterministic fakes or mocks. Cover success, malformed input, missing configuration, not-found records, and dependency failures. After every handler change, repeat the relevant event in the Lambda Console. Run frontend tests, type checks, and the Vite production build before deployment.

Create and configure API Gateway, Lambda, DynamoDB, IAM, and both S3 buckets only in the AWS Management Console.
