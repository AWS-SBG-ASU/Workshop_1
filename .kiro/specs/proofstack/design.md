# ProofStack Design

## System overview

A React/Vite/TypeScript single-page application calls an API Gateway HTTP API with payload format 2.0. Five standalone Python Lambdas use a DynamoDB metadata table and a private S3 evidence bucket. A separate public S3 bucket hosts the frontend build.

```text
Browser -> API Gateway HTTP API -> five Python Lambdas
                                      |-> DynamoDB metadata table
                                      `-> private evidence S3 bucket
Browser -> public frontend S3 bucket
```

Every data operation uses `USER#demo`. The private bucket keeps Block Public Access enabled; only built frontend assets in the separate website bucket are public.

## Components

| Component                | Responsibility                                                                                                    |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| `presign_upload` Lambda  | Validate `fileName` and `contentType`; return `uploadUrl`, `assetKey`, and `expiresIn`.                           |
| `create_evidence` Lambda | Validate metadata, generate a sortable ID, and put one DynamoDB item.                                             |
| `list_evidence` Lambda   | Query the fixed partition newest first with no pagination; optionally add temporary `assetUrl` values in phase 4. |
| `get_evidence` Lambda    | Get one item; optionally add a temporary `assetUrl` in phase 4.                                                   |
| `delete_evidence` Lambda | Get metadata, delete its exact S3 asset, then delete the DynamoDB item.                                           |
| React frontend           | Coordinate signed upload, metadata create, list, view/download, and confirmed delete.                             |

Each Lambda source is self-contained, exports `lambda_handler`, uses only the Python standard library and the Lambda-provided AWS SDK, and is directly copyable to `lambda_function.py`.

## HTTP API contract

| Route                   | Success | Main errors                                         |
| ----------------------- | ------: | --------------------------------------------------- |
| `POST /uploads/presign` |   `200` | `400`, `500`, `501` during incomplete phases        |
| `POST /evidence`        |   `201` | `400`, `500`, `501` during incomplete phases        |
| `GET /evidence`         |   `200` | `500`, `501` during incomplete phases               |
| `GET /evidence/{id}`    |   `200` | `400`, `404`, `500`, `501` during incomplete phases |
| `DELETE /evidence/{id}` |   `204` | `400`, `404`, `500`, `501` during incomplete phases |

The route variable is `id`; payload format 2.0 events use `pathParameters.id`. JSON errors always use:

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

Evidence records use `assetKey`. Phase-4 list and get responses may add `assetUrl`; temporary URLs are never stored in DynamoDB or logged.

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

1. The frontend sends `fileName` and `contentType` to the presign route.
2. Presign generates a unique `assetKey` under `evidence/demo/` and returns a short-lived PUT URL.
3. The browser uploads directly to the private bucket with the signed content type.
4. After a successful upload, the frontend creates metadata containing that `assetKey`.
5. In phase 4, list and get may generate short-lived GET URLs as `assetUrl` values.
6. Delete gets the metadata, deletes the exact object identified by `assetKey`, and then deletes the item. If S3 deletion fails, the item remains for retry.

## Configuration

| Handler | Required environment variables                                                                  |
| ------- | ----------------------------------------------------------------------------------------------- |
| Presign | `ALLOWED_ORIGIN`; phase 4: `ASSET_BUCKET`, `UPLOAD_URL_EXPIRY_SECONDS`                          |
| Create  | `ALLOWED_ORIGIN`; phase 3: `TABLE_NAME`                                                         |
| List    | `ALLOWED_ORIGIN`; phase 3: `TABLE_NAME`; phase 4: `ASSET_BUCKET`, `DOWNLOAD_URL_EXPIRY_SECONDS` |
| Get     | `ALLOWED_ORIGIN`; phase 3: `TABLE_NAME`; phase 4: `ASSET_BUCKET`, `DOWNLOAD_URL_EXPIRY_SECONDS` |
| Delete  | `ALLOWED_ORIGIN`; phase 3: `TABLE_NAME`; phase 4: `ASSET_BUCKET`                                |

Set `ALLOWED_ORIGIN=http://localhost:5173` in phase 2. Update it to the exact public website origin in phase 5. Expiry values are short positive durations such as 900 seconds.

## Least-privilege IAM

| Handler | DynamoDB                                  | Private S3              |
| ------- | ----------------------------------------- | ----------------------- |
| Presign | none                                      | `s3:PutObject`          |
| Create  | `dynamodb:PutItem`                        | none                    |
| List    | `dynamodb:Query`                          | phase 4: `s3:GetObject` |
| Get     | `dynamodb:GetItem`                        | `s3:GetObject`          |
| Delete  | `dynamodb:GetItem`, `dynamodb:DeleteItem` | `s3:DeleteObject`       |

DynamoDB permissions target the exact table ARN. S3 permissions target `arn:aws:s3:::<asset-bucket>/evidence/demo/*`. Basic Lambda logging permissions remain separate from application data permissions.

## Ordered delivery

1. Create the API Gateway HTTP API shell and configure CORS for `http://localhost:5173`.
2. Create five Lambdas, set `ALLOWED_ORIGIN`, attach payload format 2.0 integrations, and add the five routes.
3. Create DynamoDB and activate metadata operations.
4. Create the private S3 bucket and activate signed PUT/GET plus exact-object delete.
5. Build React, deploy it to the separate public S3 bucket, add its website origin to API Gateway and private-bucket CORS, and update `ALLOWED_ORIGIN`.

## Frontend and verification

Keep API types and requests in one typed client. Presentation components do not coordinate multi-step upload/create behavior. Read the API base URL from `VITE_API_BASE_URL`; never embed AWS credentials or private resource names.

Use test-driven development. Local Lambda tests use payload format 2.0 events and replace AWS SDK clients with deterministic fakes or mocks. Cover success, malformed input, missing configuration, not-found records, and dependency failures. After every handler change, repeat the relevant event in the Lambda Console. Run frontend tests, type checks, and the Vite production build before deployment.

Create and configure API Gateway, Lambda, DynamoDB, IAM, and both S3 buckets only in the AWS Management Console.