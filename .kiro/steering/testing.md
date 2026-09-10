---
inclusion: fileMatch
fileMatchPattern: ["backend/**/test_*.py", "backend/**/*_test.py", "frontend/**/*.test.ts", "frontend/**/*.test.tsx", "frontend/**/*.spec.ts", "frontend/**/*.spec.tsx"]
---

# Testing

Follow test-driven development: add or update a focused failing test, make the smallest behavior change, then refactor with the suite passing.

## Lambda tests

- Build API Gateway REST API Lambda proxy events with top-level `httpMethod`, `path`, and `resource`, plus `requestContext.stage = "prod"`; item events use `pathParameters.id`.
- Assert request normalization reads those REST proxy fields and JSON-string request bodies correctly.
- Cover success, malformed JSON, missing and invalid fields, absent path parameters, not-found data, missing configuration, and AWS dependency failures.
- Assert missing required resource variables return `500` with `error.code = CONFIGURATION_ERROR`.
- Assert an unfinished operation returns `501` with `error.code = NOT_IMPLEMENTED` only after all configuration required by that operation is present.
- Assert all error bodies match `{"error":{"code":"...","message":"..."}}` and successful delete returns an empty `204`.
- Presign tests use `fileName` and `contentType` and validate `uploadUrl`, `assetKey`, and `expiresIn` without snapshotting signed URLs.
- Create tests assert a compact UTC timestamp plus UUID segment for `id`, `SK = EVIDENCE#<id>`, and `assetKey` under `evidence/demo/`.
- List tests assert Query rather than Scan, descending sort-key order, no pagination, no internal keys, and optional phase-4 `assetUrl` values.
- Get tests assert GetItem and an optional phase-4 `assetUrl`. Delete tests assert GetItem, exact-object S3 deletion, then DeleteItem.
- Replace DynamoDB and S3 calls with deterministic fakes or mocks; local tests must not require AWS credentials or network access.
- Assert status code, headers, parsed body, AWS call parameters, and the absence of internal keys or unsafe error details.
- After every handler change, run the local test and the corresponding REST proxy event in the Lambda Console. Record the event and expected result.

## Frontend tests

- Test the typed API client for a configured REST API base ending in `/prod`, URL joining without duplicate slashes, method, body, success, empty `204`, and normalized error behavior.
- Test upload ordering so metadata creation occurs only after a successful S3 PUT.
- Test the unpaginated newest-first list plus loading, empty, failure, detail/download, and confirmed delete flows through user-visible behavior.
- Keep tests deterministic and mock requests at the network boundary.

Before delivery, run focused tests, full local suites, TypeScript validation, and the Vite production build.
