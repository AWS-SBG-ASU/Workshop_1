---
inclusion: fileMatch
fileMatchPattern: ["backend/**/*.py"]
---

# Lambda Conventions

- Keep each handler file self-contained and directly copyable to Lambda Console `lambda_function.py`.
- Model normalized HTTP requests with `ApiRequest.from_event(event)` and API Gateway responses with `ApiResponse(...).to_dict()`; do not reintroduce standalone parser or response-builder functions.
- Export `lambda_handler(event, context)` and avoid project-local runtime imports.
- Normalize API Gateway REST API Lambda proxy events from top-level `httpMethod`, `path`, `resource`, `pathParameters`, and `requestContext.stage`. Parameterized resources read `pathParameters.id`; Lambda Console events set the stage to `prod`.
- Use `USER#demo` internally; never trust a caller-supplied user key.
- Use `assetKey`. Asset keys must start with `evidence/demo/`; temporary signed downloads may be returned as `assetUrl` but are never stored or logged.
- Validate and normalize input before AWS calls. Return `400` for invalid requests, `404` for absent records, and safe `500` responses for dependency failures.
- Return errors only as `{"error":{"code":"...","message":"..."}}`. A missing required variable returns `500 CONFIGURATION_ERROR`; an unfinished operation with all required configuration returns `501 NOT_IMPLEMENTED`.
- Return JSON with `Content-Type: application/json` and the configured CORS origin; a successful delete returns an empty `204`. Lambda response CORS complements, but does not replace, REST `OPTIONS` MOCK responses and `DEFAULT_4XX`/`DEFAULT_5XX` Gateway Response CORS.
- Use only `TABLE_NAME`, `ASSET_BUCKET`, `ALLOWED_ORIGIN`, `UPLOAD_URL_EXPIRY_SECONDS`, and `DOWNLOAD_URL_EXPIRY_SECONDS` for Lambda deployment configuration.
- List uses DynamoDB Query, never Scan, in descending sort-key order and returns no pagination token.
- Generate `id` as a compact fixed-width UTC timestamp followed by a UUID segment and store `SK = EVIDENCE#<id>`.
- Delete reads metadata, deletes the exact S3 key first, and calls DeleteItem only after S3 succeeds.
- Create AWS SDK clients in a way local tests can replace without contacting AWS.
- Use structured, concise logs. Do not log request bodies, internal keys, credentials, file content, raw dependency errors, or presigned URLs.
- Write the failing local test first. After every handler change, run local tests and a Lambda Console test using a REST API Lambda proxy event for stage `prod`.
- Keep IAM requirements adjacent to the handler handoff and list exact actions and resources.
