# Lambda Console testing

Use API Gateway HTTP API payload format 2.0 test events after every handler copy or edit. Test event shape, method, path, JSON body, and path parameters without changing deployed routes.

## Run an event

1. Open the function in the Lambda Console in `us-east-1` and choose **Test**.
2. Choose **Create new event**, give it a descriptive name, and use **Event JSON**.
3. Copy the matching checked-in event into the editor and save it.
4. Confirm item events use `rawPath` such as `/evidence/demo-id` and `pathParameters.id`.
5. Choose **Test** and inspect the returned status, headers, and body. Do not put credentials, live presigned URLs, private file content, or internal keys in saved events or logs.

| Lambda                       | Event                                         |
| ---------------------------- | --------------------------------------------- |
| `proofstack-presign-upload`  | `backend/events/post_uploads_presign.json`    |
| `proofstack-create-evidence` | `backend/events/post_evidence.json`           |
| `proofstack-list-evidence`   | `backend/events/get_evidence.json`            |
| `proofstack-get-evidence`    | `backend/events/get_evidence_demo_id.json`    |
| `proofstack-delete-evidence` | `backend/events/delete_evidence_demo_id.json` |

## Phase-specific expected results

All error responses use:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Safe operation-specific message"
  }
}
```

- **Before a future resource variable is configured:** an affected handler returns `statusCode: 500` with `error.code = CONFIGURATION_ERROR`.
- **After every variable required by an unfinished operation is configured:** the handler returns `statusCode: 501` with `error.code = NOT_IMPLEMENTED`.
- **After implementation:** replace the corresponding incomplete-operation expectation with the route's success and failure cases.

`ALLOWED_ORIGIN` is configured on all five handlers in phase 2. `TABLE_NAME` is added to create, list, get, and delete in phase 3. `ASSET_BUCKET`, `UPLOAD_URL_EXPIRY_SECONDS`, and `DOWNLOAD_URL_EXPIRY_SECONDS` are added to the applicable handlers in phase 4.

The Lambda Console may label an invocation successful even when the application response is `400`, `404`, `500`, or `501`; inspect `statusCode` and parse the body.

## Implemented operation expectations

- **Presign:** expect `200`; send `fileName` and `contentType`; validate `uploadUrl`, `assetKey` under `evidence/demo/`, and `expiresIn`. Do not snapshot or log the URL.
- **Create:** expect `201`; validate a compact UTC timestamp plus UUID segment for `id`, `assetKey`, and a public evidence response without `PK` or `SK`. The application data permission is `dynamodb:PutItem` only.
- **List:** expect `200` with all `items`, no pagination token, and no internal keys. Assert DynamoDB Query rather than Scan and descending sort-key order. In phase 4, records may include temporary `assetUrl` values.
- **Get:** expect `200` for `pathParameters.id` and retain `404` coverage. In phase 4, the record may include a temporary `assetUrl`.
- **Delete:** expect GetItem, deletion of the exact S3 `assetKey`, then DeleteItem. Return an empty `204` only after S3 and DynamoDB succeed; retain not-found and dependency-failure cases.

Mock AWS SDK calls in local tests so they do not modify AWS resources. Run:

```text
python -m pytest -c backend/pytest.ini backend/tests
```

Update the saved Lambda Console expectation after each handler change. Use disposable demo payloads and perform the record/file lifecycle through the handler or browser application.