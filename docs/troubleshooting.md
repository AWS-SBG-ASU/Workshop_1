# Troubleshooting

Start with the browser Network panel, then API Gateway access logs and the Lambda's CloudWatch log stream. Record request IDs, status codes, and resource names, but never log credentials, raw dependency errors, file contents, internal DynamoDB keys, or presigned URLs.

## CORS errors

- In phase 1, API Gateway CORS allows `http://localhost:5173`, methods `GET`, `POST`, `DELETE`, and `OPTIONS`, and headers `content-type` and `accept`.
- In phase 5, add the exact S3 website origin alongside localhost. An S3 website origin uses `http://`.
- Set `ALLOWED_ORIGIN=http://localhost:5173` on all five Lambdas in phase 2. For deployed website responses, update it to the exact website origin in phase 5.
- The private asset bucket has a separate CORS rule for browser `PUT`, `GET`, and `HEAD`. Add the website origin in phase 5 and keep Block Public Access enabled.
- After an origin change, confirm the `$default` API stage auto-deployed and retry without a stale browser cache.

## 403 Forbidden

**API request:** Verify the route has the correct Lambda integration, API Gateway can invoke that function, and the invoke URL uses the deployed stage.

**Presigned S3 request:** Verify the URL has not expired, `ASSET_BUCKET` names the private evidence bucket, and the key starts with `evidence/demo/`. Presign needs `s3:PutObject`; list and get need `s3:GetObject`; delete needs `s3:DeleteObject`. Scope each permission to `arn:aws:s3:::<asset-bucket>/evidence/demo/*`.

**Website object:** Verify public access was enabled only for the website bucket and its bucket policy grants `s3:GetObject` on `arn:aws:s3:::<website-bucket>/*`.

## 404 Not Found

- Match routes exactly: `POST /uploads/presign`, `POST /evidence`, `GET /evidence`, `GET /evidence/{id}`, and `DELETE /evidence/{id}`.
- Item routes use the variable `id`; payload format 2.0 events contain `pathParameters.id`.
- A valid route returns an application `404` when `PK = USER#demo` and `SK = EVIDENCE#<id>` do not identify a record.
- For the website, ensure `index.html` is at the bucket root and both index and error documents are `index.html`.

## 500 CONFIGURATION_ERROR

A handler missing a variable required for its current operation returns a controlled `500` with this shape:

```json
{"error":{"code":"CONFIGURATION_ERROR","message":"Safe configuration message"}}
```

Check exact variable names, values, function region, and role policy resource ARNs. Do not return raw environment values or dependency messages.

| Function | Required variables by completed phase                                                                    |
| -------- | -------------------------------------------------------------------------------------------------------- |
| Presign  | phase 2: `ALLOWED_ORIGIN`; phase 4: `ASSET_BUCKET`, `UPLOAD_URL_EXPIRY_SECONDS`                          |
| Create   | phase 2: `ALLOWED_ORIGIN`; phase 3: `TABLE_NAME`                                                         |
| List     | phase 2: `ALLOWED_ORIGIN`; phase 3: `TABLE_NAME`; phase 4: `ASSET_BUCKET`, `DOWNLOAD_URL_EXPIRY_SECONDS` |
| Get      | phase 2: `ALLOWED_ORIGIN`; phase 3: `TABLE_NAME`; phase 4: `ASSET_BUCKET`, `DOWNLOAD_URL_EXPIRY_SECONDS` |
| Delete   | phase 2: `ALLOWED_ORIGIN`; phase 3: `TABLE_NAME`; phase 4: `ASSET_BUCKET`                                |

## 501 NOT_IMPLEMENTED

A `501` with `error.code = NOT_IMPLEMENTED` means every variable required by that operation is present but its behavior is unfinished. If required future resource variables are absent, expect `500 CONFIGURATION_ERROR` instead.

## DynamoDB behavior

- Confirm key names are string attributes `PK` and `SK` and every operation uses `USER#demo`.
- Evidence sort keys are `EVIDENCE#<id>`, where `id` is a compact fixed-width UTC timestamp followed by a UUID segment.
- List must use Query, never Scan, with descending sort-key order. It returns all matching records without pagination.
- IAM is exact: create `dynamodb:PutItem`; list `dynamodb:Query`; get `dynamodb:GetItem`; delete `dynamodb:GetItem` and `dynamodb:DeleteItem`.

## Presigned upload content type

The presign request sends `fileName` and `contentType`. The response contains `uploadUrl`, `assetKey`, and `expiresIn`. The PUT content type must exactly match the signed value; a mismatch can produce `403 SignatureDoesNotMatch`. Use the URL before `expiresIn` elapses and send `PUT`, not `POST`.

## Missing download link

Phase-4 list and get responses may include temporary `assetUrl` values. Confirm `ASSET_BUCKET` and `DOWNLOAD_URL_EXPIRY_SECONDS` are set on both functions, their roles have `s3:GetObject` on `evidence/demo/*`, and the stored record contains `assetKey`. Never persist or log `assetUrl`.

## Delete failure

Delete must GetItem, read `assetKey`, delete that exact S3 object, and only then call DeleteItem. If S3 deletion fails, the DynamoDB item remains. Confirm the delete role has `s3:DeleteObject` for the prefix and `dynamodb:GetItem` plus `dynamodb:DeleteItem` for the exact table.

## Wrong route integration

In API Gateway, select each route and inspect **Attached integration**. Verify presign → `proofstack-presign-upload`, create → `proofstack-create-evidence`, list → `proofstack-list-evidence`, get → `proofstack-get-evidence`, and delete → `proofstack-delete-evidence`. Confirm payload format version 2.0 and verify the API appears under each Lambda's triggers.

## S3 website issues

- Use the S3 **website endpoint**, not the bucket REST endpoint.
- Upload the contents of `frontend/dist/`, not the directory itself.
- Confirm `index.html` exists at the bucket root and references uploaded assets.
- A blank page can indicate a missing or incorrect `VITE_API_BASE_URL`; inspect the browser console and rebuild.
- S3 website hosting is HTTP-only. If HTTPS is required, place an HTTPS-capable delivery service in front of the website before using a secure custom domain.