# Lambda Console testing

Use API Gateway REST API Lambda proxy test events after every handler copy or edit. Test event shape, method, path, JSON body, and path parameters without changing deployed resources or methods.

## REST proxy event contract

Every saved event contains top-level `httpMethod`, actual `path`, templated `resource`, headers, `requestContext.stage` set to `prod`, and `isBase64Encoded: false`. Item events contain `pathParameters.id`; collection events use `pathParameters: null`. Request bodies are JSON strings when present and `null` otherwise.

Representative item event:

```json
{
  "httpMethod": "GET",
  "path": "/evidence/demo-id",
  "resource": "/evidence/{id}",
  "headers": {
    "accept": "application/json"
  },
  "pathParameters": {
    "id": "demo-id"
  },
  "requestContext": {
    "stage": "prod"
  },
  "body": null,
  "isBase64Encoded": false
}
```

Representative JSON-body event:

```json
{
  "httpMethod": "POST",
  "path": "/uploads/presign",
  "resource": "/uploads/presign",
  "headers": {
    "accept": "application/json",
    "content-type": "application/json"
  },
  "pathParameters": null,
  "requestContext": {
    "stage": "prod"
  },
  "body": "{\"fileName\":\"receipt.pdf\",\"contentType\":\"application/pdf\"}",
  "isBase64Encoded": false
}
```

## Run an event

1. Open the function in the Lambda Console in `us-east-1` and choose **Test**.
2. Choose **Create new event**, give it a descriptive name, and use **Event JSON**.
3. Build the event from the REST proxy contract above with the exact method and resource for the function.
4. For item events, set the concrete `path` such as `/evidence/demo-id`, templated `resource` to `/evidence/{id}`, and `pathParameters.id` to the same sample ID.
5. Choose **Test** and inspect the returned status, headers, and body. Do not put credentials, live presigned URLs, private file content, or internal keys in saved events or logs.

| Lambda                       | Method and resource     |
| ---------------------------- | ----------------------- |
| `proofstack-presign-upload`  | `POST /uploads/presign` |
| `proofstack-create-evidence` | `POST /evidence`        |
| `proofstack-list-evidence`   | `GET /evidence`         |
| `proofstack-get-evidence`    | `GET /evidence/{id}`    |
| `proofstack-delete-evidence` | `DELETE /evidence/{id}` |

A direct Lambda Console invocation validates handler behavior but does not deploy API changes. If a REST resource, method, integration, CORS response, or Gateway Response changed, explicitly redeploy API stage `prod` and then test the invoke base ending in `/prod`.

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
- **After implementation:** replace the corresponding incomplete-operation expectation with the method's success and failure cases.

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
