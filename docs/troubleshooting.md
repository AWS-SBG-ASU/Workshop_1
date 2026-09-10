# Troubleshooting

Start with the browser Network panel, the Lambda's CloudWatch log stream, and the API Gateway deployed method and integration settings. Record request IDs, status codes, and resource names, but never log credentials, raw dependency errors, file contents, internal DynamoDB keys, or signed URLs.

## CORS errors

- Confirm each callable final resource has an `OPTIONS` method with **Authorization** `NONE`, **API Key Required** false, and a `MOCK` integration returning `200`.
- Confirm exact allow-method values: `/uploads/presign` uses `POST,OPTIONS`; `/evidence` uses `GET,POST,OPTIONS`; `/evidence/{id}` uses `GET,DELETE,OPTIONS`.
- Confirm `Access-Control-Allow-Headers` is `content-type,accept` and the integration-response origin exactly matches the browser origin.
- Confirm Gateway Responses `DEFAULT_4XX` and `DEFAULT_5XX` contain CORS headers; otherwise gateway-generated errors can appear as browser CORS failures.
- In phase 2, set `ALLOWED_ORIGIN=http://localhost:5173` only on the temporary `proofstack-list-evidence` `/workshop` function. In phase 3/Prompt 1, use it on all four metadata functions. In phase 4/Prompt 2, add it to `proofstack-presign-upload`, so all five final handlers then have it.
- In phase 5, replace every Lambda `ALLOWED_ORIGIN` with the exact S3 website origin, which uses `http://`.
- In phase 5, replace localhost in REST `OPTIONS` and both default Gateway Responses with the website origin. Do not retain localhost there for the deployed website configuration.
- The private asset bucket has separate CORS for direct browser `PUT`, `GET`, and `HEAD`; it may retain both localhost and the website origin while Block Public Access remains enabled.
- After any API CORS change, explicitly redeploy stage `prod` and retry without a stale browser cache.

## 403 Forbidden

**API request:** Verify the Regional REST API has the exact resource and method, the method has **Authorization** `NONE` and **API Key Required** false, API Gateway can invoke the selected Lambda, and the request URL includes `/prod`.

**Presigned S3 request:** Verify the URL has not expired, `ASSET_BUCKET` names the private evidence bucket, and the key starts with `evidence/demo/`. Presign needs `s3:PutObject`; list and get need `s3:GetObject`; delete needs `s3:DeleteObject`. Scope each permission to `arn:aws:s3:::<asset-bucket>/evidence/demo/*`.

**Website object:** Verify public access was enabled only for the website bucket and its bucket policy grants `s3:GetObject` on `arn:aws:s3:::<website-bucket>/*`.

## 404 Not Found

- Match final methods and resources exactly: `POST /uploads/presign`, `POST /evidence`, `GET /evidence`, `GET /evidence/{id}`, and `DELETE /evidence/{id}`.
- Confirm the invoke URL includes named stage `/prod`, and redeploy `prod` after adding or changing a resource or method.
- Item resources use the variable `id`; REST proxy events contain `pathParameters.id`.
- A valid metadata method returns an application `404` when `PK = USER#demo` and `SK = EVIDENCE#<id>` do not identify a record.
- For the website, ensure `index.html` is at the bucket root and both index and error documents are `index.html`.

## 500 CONFIGURATION_ERROR

A handler missing a variable required for its current operation returns a controlled `500` with this shape:

```json
{"error":{"code":"CONFIGURATION_ERROR","message":"Safe configuration message"}}
```

Check exact variable names, values, function region, and role policy resource ARNs. Do not return raw environment values or dependency messages.

| Function | Required variables by completed phase                                                                                                           |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Presign  | phase 4/Prompt 2: `ALLOWED_ORIGIN`, `ASSET_BUCKET`, `UPLOAD_URL_EXPIRY_SECONDS`                                                                 |
| Create   | phase 3/Prompt 1: `ALLOWED_ORIGIN`, `TABLE_NAME`                                                                                                |
| List     | phase 2 basic lesson: `ALLOWED_ORIGIN`; phase 3/Prompt 1 adds `TABLE_NAME`; phase 4/Prompt 2 adds `ASSET_BUCKET`, `DOWNLOAD_URL_EXPIRY_SECONDS` |
| Get      | phase 3/Prompt 1: `ALLOWED_ORIGIN`, `TABLE_NAME`; phase 4/Prompt 2 adds `ASSET_BUCKET`, `DOWNLOAD_URL_EXPIRY_SECONDS`                           |
| Delete   | phase 3/Prompt 1: `ALLOWED_ORIGIN`, `TABLE_NAME`; phase 4/Prompt 2 adds `ASSET_BUCKET`                                                          |

Prompt 3 adds no Lambda variables. Across the final phase-4 functions, use only `TABLE_NAME`, `ASSET_BUCKET`, `ALLOWED_ORIGIN`, `UPLOAD_URL_EXPIRY_SECONDS`, and `DOWNLOAD_URL_EXPIRY_SECONDS`.

## 501 NOT_IMPLEMENTED

A `501` with `error.code = NOT_IMPLEMENTED` means every variable required by that current operation is present but its behavior is intentionally unfinished. In phase 3/Prompt 1, an existing-item delete returns this response after GetItem because S3-first deletion is not available yet. The presign function is not implemented or configured until phase 4/Prompt 2. If a variable required for a current implemented operation is absent, expect `500 CONFIGURATION_ERROR` instead.

## DynamoDB behavior

- Confirm key names are string attributes `PK` and `SK` and every operation uses `USER#demo`.
- Evidence sort keys are `EVIDENCE#<id>`, where `id` is a compact fixed-width UTC timestamp followed by a UUID segment.
- List must use Query, never Scan, with descending sort-key order. It returns all matching records without pagination.
- In phase 3/Prompt 1, exact-table IAM is create `dynamodb:PutItem`; list `dynamodb:Query`; get `dynamodb:GetItem`; delete `dynamodb:GetItem` only.
- In phase 4/Prompt 2, add `dynamodb:DeleteItem` to delete only after exact-object S3-first deletion is implemented. Create remains PutItem-only.

## Presigned upload content type

Phase 4/Prompt 2 implements presign. The request sends `fileName` and `contentType`; the response contains `uploadUrl`, `assetKey`, and `expiresIn`. The PUT content type must exactly match the signed value; a mismatch can produce `403 SignatureDoesNotMatch`. Use the URL before `expiresIn` elapses and send `PUT`, not `POST`.

## Missing download link

Phase-4/Prompt-2 list and get responses may include temporary `assetUrl` values. Confirm `ASSET_BUCKET` and `DOWNLOAD_URL_EXPIRY_SECONDS` are set on both functions, their roles have `s3:GetObject` on `evidence/demo/*`, and the stored record contains `assetKey`. Never persist or log `assetUrl`.

## Delete failure

In phase 3/Prompt 1, delete performs GetItem only. For a found record with a valid `assetKey`, it returns controlled `501 NOT_IMPLEMENTED`; the item must remain and neither S3 nor DeleteItem may be called.

In phase 4/Prompt 2, delete must GetItem, read `assetKey`, delete that exact S3 object, and only then call DeleteItem. If S3 deletion fails, the DynamoDB item remains. Confirm the delete role has `s3:DeleteObject` for `arn:aws:s3:::<asset-bucket>/evidence/demo/*` and `dynamodb:GetItem` plus `dynamodb:DeleteItem` for the exact table.

## Wrong method integration

In API Gateway, open `ProofStackApi` → **Resources**, select each final business method, and inspect its integration request. Verify presign → `proofstack-presign-upload`, create → `proofstack-create-evidence`, list → `proofstack-list-evidence`, get → `proofstack-get-evidence`, and delete → `proofstack-delete-evidence`. Confirm **Lambda proxy integration** is enabled, **Authorization** is `NONE`, **API Key Required** is false, and the API appears under each Lambda's triggers. Redeploy `prod` after corrections.

A matching Lambda Console event has top-level `httpMethod`, concrete `path`, templated `resource`, `requestContext.stage = "prod"`, and `pathParameters.id` for item methods. A direct Lambda test does not prove the API's deployed method points to that function.

During phase 2, troubleshoot only the temporary `proofstack-list-evidence` `GET /workshop` lesson. Prompt 1 replaces that code and phase 3 uses the final `GET /evidence` integration and event.

## Frontend build and S3 website issues

Prompt 3 verifies the React flow, typed client, tests, type checking, and production build before hosting. A build failure is local frontend readiness work; Prompt 3 does not provision AWS or publish files.

For the later Console-only phase-5 hosting step:

- Use the S3 **website endpoint**, not the bucket REST endpoint.
- Upload the contents of `frontend/dist/`, not the directory itself.
- Confirm `index.html` exists at the bucket root and references uploaded assets.
- A blank page can indicate a missing or incorrect `VITE_API_BASE_URL`; confirm it is the API invoke base ending in `/prod`, inspect the browser console, and rebuild.
- S3 website hosting is HTTP-only.