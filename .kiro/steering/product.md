---
inclusion: always
---

# ProofStack Product

ProofStack is a personal evidence application for one fixed demo user. It supports uploading a private file, saving descriptive evidence metadata, browsing records, downloading through temporary links, and deleting both the record and its file.

## Product contract

- Use `USER#demo` for every data operation. Do not add authentication, registration, accounts, sharing, or multi-user behavior.
- Keep the five routes stable:
  - `POST /uploads/presign`
  - `POST /evidence`
  - `GET /evidence`
  - `GET /evidence/{id}`
  - `DELETE /evidence/{id}`
- Use `id` as the resource parameter and `pathParameters.id` in REST API Lambda proxy events. Such events use top-level `httpMethod`, `path`, and `resource`, with `requestContext.stage = "prod"`.
- Presign accepts `fileName` and `contentType` and returns `uploadUrl`, `assetKey`, and `expiresIn`.
- Evidence records use `assetKey`; phase-4 list and get responses may include temporary `assetUrl` values.
- Keep evidence files private under `evidence/demo/`. Browser upload and download use short-lived presigned URLs.
- List uses DynamoDB Query, never Scan, returns records newest first, and does not paginate.
- Delete the exact S3 asset before deleting its DynamoDB item.
- Return errors as `{"error":{"code":"...","message":"..."}}`; only a successful `204` delete has no body.
- Make empty, loading, success, validation, not-found, dependency-failure, and delete-confirmation states clear.
- Do not expose internal DynamoDB keys, credentials, raw dependency errors, or presigned URLs in logs.
