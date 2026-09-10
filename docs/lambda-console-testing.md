# Lambda Console testing

Use API Gateway REST API Lambda proxy test events after every handler copy or edit. Test event shape, method, path, JSON body, and path parameters without changing deployed resources or methods.

## REST proxy event contract

Every final-route saved event contains top-level `httpMethod`, actual `path`, templated `resource`, headers, `requestContext.stage` set to `prod`, and `isBase64Encoded: false`. Item events contain `pathParameters.id`; collection events use `pathParameters: null`. Request bodies are JSON strings when present and `null` otherwise.

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
5. Choose **Test** and inspect the returned status, headers, and body. Do not put credentials, live signed URLs, private file content, or internal keys in saved events or logs.

| Lambda                       | Final method and resource |
| ---------------------------- | ------------------------- |
| `proofstack-presign-upload`  | `POST /uploads/presign`   |
| `proofstack-create-evidence` | `POST /evidence`          |
| `proofstack-list-evidence`   | `GET /evidence`           |
| `proofstack-get-evidence`    | `GET /evidence/{id}`      |
| `proofstack-delete-evidence` | `DELETE /evidence/{id}`   |

The checked-in files under `backend/events/` describe these final routes and remain the reusable events for phases 3 and 4.

A direct Lambda Console invocation validates handler behavior but does not deploy API changes. If a REST resource, method, integration, CORS response, or Gateway Response changed, explicitly redeploy API stage `prod` and then test the invoke base ending in `/prod`.

## Phase 2 — temporary basic Lambda lesson

Phase 2 tests only the temporary `proofstack-list-evidence` `/workshop` lesson. Configure `ALLOWED_ORIGIN=http://localhost:5173` on that function only. Do not configure the other final handlers or save an additional checked-in event for this temporary route.

Build the temporary event inline with `httpMethod: "GET"`, `path: "/workshop"`, `resource: "/workshop"`, `pathParameters: null`, `requestContext.stage: "prod"`, `body: null`, and `isBase64Encoded: false`. Its expected response is the basic lesson response documented by the phase-2 runbook. Prompt 1 replaces this temporary list code; do not continue using the `/workshop` event to validate final metadata behavior.

## Phase 3 / Prompt 1 — metadata handlers

After the DynamoDB table is created, configure `ALLOWED_ORIGIN` and `TABLE_NAME` on create, list, get, and delete. The list function retains its phase-2 `ALLOWED_ORIGIN` value while its temporary `/workshop` code is replaced. Do not configure or test the presign function in this phase, and do not add S3 variables.

Run final-route checked-in events for every changed metadata handler:

- **Create:** expect `201`, a compact fixed-width UTC timestamp plus UUID segment for `id`, stored `assetKey`, and a public response without `PK` or `SK`. The only application data permission is `dynamodb:PutItem`.
- **List:** expect `200` with all `items`, no pagination token, internal key, or `assetUrl`. Confirm DynamoDB Query rather than Scan and descending sort-key order. Its application permission is `dynamodb:Query`.
- **Get:** expect `200` for a known `pathParameters.id` and retain `404` coverage. Its application permission is `dynamodb:GetItem`.
- **Delete:** expect GetItem and `404` when absent. For an existing item with a valid stored key, expect controlled `501 NOT_IMPLEMENTED`; confirm no DeleteItem call occurs and metadata remains. Its application permission is only `dynamodb:GetItem`.

Also retain malformed-event/input `400`, wrong-route `404`, missing-current-configuration `500 CONFIGURATION_ERROR`, and sanitized DynamoDB-failure `500` cases. All error responses use:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Safe operation-specific message"
  }
}
```

## Phase 4 / Prompt 2 — private S3 lifecycle

Phase 4 uses all five permitted Lambda variable names across the applicable functions: `TABLE_NAME`, `ASSET_BUCKET`, `ALLOWED_ORIGIN`, `UPLOAD_URL_EXPIRY_SECONDS`, and `DOWNLOAD_URL_EXPIRY_SECONDS`.

- Configure presign with `ALLOWED_ORIGIN`, `ASSET_BUCKET`, and `UPLOAD_URL_EXPIRY_SECONDS`, then deploy and test the final `proofstack-presign-upload` function.
- Keep create on `ALLOWED_ORIGIN` and `TABLE_NAME` only.
- Add `ASSET_BUCKET` and `DOWNLOAD_URL_EXPIRY_SECONDS` to list and get while retaining their phase-3 values.
- Add `ASSET_BUCKET` to delete while retaining its phase-3 values.

Run the checked-in final-route events for changed handlers:

- **Presign:** expect `200`; send `fileName` and `contentType`; validate `uploadUrl`, `assetKey` under `evidence/demo/`, and numeric `expiresIn`. Do not snapshot, save, or log the URL.
- **List/Get:** preserve the phase-3 DynamoDB expectations; responses may now include fresh temporary `assetUrl` values. Do not persist or log them.
- **Delete:** expect GetItem, deletion of the exact S3 `assetKey`, then DeleteItem. Return an empty `204` only after S3 and DynamoDB succeed. Retain `404` and sanitized dependency-failure coverage, and confirm an S3 failure leaves metadata intact.

A future variable that is absent must not be required before its phase. Once a variable is required for the current operation, absence returns controlled `500 CONFIGURATION_ERROR`; configured but intentionally unfinished phase-3 delete returns controlled `501 NOT_IMPLEMENTED`.

## Phase 5 / Prompt 3 — frontend readiness

Prompt 3 changes no Lambda handler or environment variable, so it requires no new Lambda Console event or handoff. Use frontend tests, TypeScript validation, production build, and deployed `/prod` browser verification. The later Console hosting runbook performs website-origin CORS changes and the required `prod` redeployment.

Mock AWS SDK calls in local backend tests so they do not modify AWS resources. After actual handler changes, run:

```text
python -m pytest -c backend/pytest.ini backend/tests
```

Update the saved Lambda Console expectation after each handler change. Use disposable demo payloads and perform the final record/file lifecycle through the handler or browser application.