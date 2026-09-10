# AWS Console setup

Build ProofStack service by service in the AWS Management Console in `us-east-1`. Do not use AWS CLI, CloudShell provisioning commands, IaC, or deployment scripts. Replace `<ACCOUNT_ID>` and `<API_ID>` only with AWS-generated values; keep generated names, ARNs, endpoints, credentials, and presigned URLs out of version control.

Every business method and `OPTIONS` method uses **Authorization** `NONE` and **API Key Required** false. Every business method uses Lambda proxy integration. After any API resource, method, integration, `OPTIONS`, CORS, or Gateway Response change, explicitly choose **Deploy API** for stage `prod`.

## Phase 1 — Learn API Gateway without application services

API Gateway is the HTTP front door. A REST API contains path **resources** and HTTP **methods**; an **integration** supplies a method response. A browser’s CORS **preflight** is an `OPTIONS` request. **Gateway Responses** cover API Gateway’s own errors. A **deployment** snapshots saved configuration into a named **stage** such as `prod`.

1. Create a **Regional REST API** named `ProofStackApi` in `us-east-1`.
2. Do not create any final ProofStack route yet. Create only disposable `/workshop`.
3. Create `GET /workshop` with **Mock** integration, `NONE`, and no API key.
4. In Integration Request, set `application/json` template `{"statusCode": 200}`.
5. In Method Response, declare `200` and `Content-Type`.
6. In Integration Response, map `Content-Type` to `'application/json'` and add `application/json` body template:

```json
{"message":"API Gateway is live"}
```

7. Create `OPTIONS /workshop` with **Mock**, `NONE`, and no API key. Use Integration Request template `{"statusCode": 200}`; declare the three CORS headers in Method Response `200`; map them in Integration Response to:
   - origin `'http://localhost:5173'`
   - headers `'content-type,accept'`
   - methods `'GET,OPTIONS'`
8. Set both `DEFAULT_4XX` and `DEFAULT_5XX` Gateway Responses to the same origin/headers/methods.
9. Deploy to new stage `prod`, record `https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod`, and open `/prod/workshop`. Expect `{"message":"API Gateway is live"}`.

## Phase 2 — Connect the first Lambda

Lambda runs request-driven code. Proxy integration passes the complete REST request event to Lambda and relays Lambda’s `statusCode`, `headers`, and string `body`.

1. Create only `proofstack-list-evidence`: Python 3.12, x86_64, handler `lambda_function.lambda_handler`, 256 MB, 10 seconds, and a new basic Console-created execution role.
2. Set `ALLOWED_ORIGIN=http://localhost:5173`.
3. Paste this temporary standalone `lambda_function.py` and deploy:

```python
import json
import os


def lambda_handler(event, context):
    valid = (
        isinstance(event, dict)
        and event.get("httpMethod") == "GET"
        and event.get("path") == "/workshop"
        and event.get("resource") == "/workshop"
        and (event.get("requestContext") or {}).get("stage") == "prod"
    )
    status = 200 if valid else 404
    payload = (
        {"message": "Lambda is connected"}
        if valid
        else {"error": {"code": "NOT_FOUND", "message": "Route not found."}}
    )
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": os.environ.get("ALLOWED_ORIGIN", "null"),
            "Access-Control-Allow-Headers": "content-type,accept",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps(payload, separators=(",", ":")),
    }
```

4. Run this Lambda Console event because handler code changed:

```json
{
  "httpMethod": "GET",
  "path": "/workshop",
  "resource": "/workshop",
  "headers": {"Accept": "application/json"},
  "pathParameters": null,
  "requestContext": {"stage": "prod"},
  "body": null,
  "isBase64Encoded": false
}
```

Expect `200`, localhost CORS, and `{"message":"Lambda is connected"}`.

5. Delete only the MOCK `GET /workshop`, recreate `GET` with Lambda proxy integration to `proofstack-list-evidence`, keep `OPTIONS` MOCK, allow invoke permission, and redeploy `prod`.
6. `/prod/workshop` now returns the Lambda message. API Gateway owns routing/preflight/deployment; Lambda owns request validation and response content.

## Phase 3 — Add DynamoDB metadata and real evidence routes

DynamoDB stores durable items. Create table `ProofStackEvidence` with string partition key `PK`, string sort key `SK`, and on-demand capacity. ProofStack always uses `PK=USER#demo`; evidence sort keys are `SK=EVIDENCE#<id>`. Timestamp-first fixed-width IDs plus UUID segments make a descending DynamoDB Query return newest first. List uses Query, never Scan, and does not paginate.

1. Before copying handlers, complete **Prompt 1 — Implement DynamoDB evidence metadata** in [the attendee workbook](attendee-implementation-prompts.internal.md) (`prompt_store/01.txt`). Repository handlers begin as `501 NOT_IMPLEMENTED` scaffolds and must be implemented and locally tested.
2. Create `ProofStackEvidence` and record `arn:aws:dynamodb:us-east-1:<ACCOUNT_ID>:table/ProofStackEvidence`.
3. Replace the temporary list code with `backend/functions/list_evidence/lambda_function.py`.
4. Create only these three additional functions now:
   - `proofstack-create-evidence` ← `backend/functions/create_evidence/lambda_function.py`
   - `proofstack-get-evidence` ← `backend/functions/get_evidence/lambda_function.py`
   - `proofstack-delete-evidence` ← `backend/functions/delete_evidence/lambda_function.py`
5. Each uses Python 3.12, x86_64, `lambda_function.lambda_handler`, 256 MB, 10 seconds, and its own basic generated role. Paste/deploy the Prompt-1 implementation.
6. Set both `ALLOWED_ORIGIN=http://localhost:5173` and `TABLE_NAME=ProofStackEvidence` on create/list/get/delete.
7. Add exact-table IAM:

| Function | Policy name                   | Action at this checkpoint |
| -------- | ----------------------------- | ------------------------- |
| Create   | `ProofStackCreateTableAccess` | `dynamodb:PutItem`        |
| List     | `ProofStackListTableAccess`   | `dynamodb:Query`          |
| Get      | `ProofStackGetTableAccess`    | `dynamodb:GetItem`        |
| Delete   | `ProofStackDeleteTableAccess` | `dynamodb:GetItem` only   |

Each policy resource is:

```text
arn:aws:dynamodb:us-east-1:<ACCOUNT_ID>:table/ProofStackEvidence
```

Do not grant `DeleteItem` or any S3 action yet.

8. Only now create `/evidence`, then child `/{id}`.
9. Create MOCK `OPTIONS` methods with Integration Request `{"statusCode": 200}`, declared CORS headers in Method Response, and these Integration Response values:

| Resource         | Origin                    | Headers                 | Methods                |
| ---------------- | ------------------------- | ----------------------- | ---------------------- |
| `/evidence`      | `'http://localhost:5173'` | `'content-type,accept'` | `'GET,POST,OPTIONS'`   |
| `/evidence/{id}` | `'http://localhost:5173'` | `'content-type,accept'` | `'GET,DELETE,OPTIONS'` |

10. Add proxy methods: `POST /evidence` → create; `GET /evidence` → list; `GET /evidence/{id}` → get; `DELETE /evidence/{id}` → delete. Use `NONE`, no API key, and allow invoke permission.
11. Update both default Gateway Responses to localhost, `content-type,accept`, and `GET,POST,DELETE,OPTIONS`; redeploy `prod`.
12. Run the matching `backend/events/` Lambda Console event for create/list/get/delete because their handler code changed. Every event has top-level `httpMethod`, `path`, `resource`, `requestContext.stage="prod"`, and item events have `pathParameters.id`.
13. Verify create `201`, list `200` newest first, get `200`/`404`, and delete’s controlled incomplete-operation response. Delete must retain metadata because private file deletion does not exist yet.
14. After evidence routes work, delete `/workshop` and redeploy `prod`. The API now has only metadata routes; no `/uploads` route and no presign function exist.

All errors retain `{"error":{"code":"...","message":"..."}}`; public records omit `PK` and `SK`.

## Phase 4 — Add private S3 and complete the lifecycle

S3 stores objects in buckets. The object key begins `evidence/demo/`. The browser uses short-lived presigned PUT/GET URLs so file bytes bypass the API and no AWS credentials enter frontend code. Bucket CORS permits these browser requests but does not make objects public.

1. Create private bucket `proofstack-assets-<ACCOUNT_ID>-us-east-1` with all Block Public Access settings on. Save CORS:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD", "PUT"],
    "AllowedOrigins": ["http://localhost:5173"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

2. Complete **Prompt 2 — Integrate private S3 evidence files** in [the attendee workbook](attendee-implementation-prompts.internal.md) (`prompt_store/02.txt`) before copying changed handlers.
3. Create the fifth/final function only now: `proofstack-presign-upload` from `backend/functions/presign_upload/lambda_function.py`, Python 3.12, x86_64, `lambda_function.lambda_handler`, 256 MB, 10 seconds, new basic role.
4. Deploy the Prompt-2 presign/list/get/delete sources; create remains unchanged.
5. Set phase-4 environments:

| Function | Environment                                                                                                                                                         |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Presign  | `ALLOWED_ORIGIN=http://localhost:5173`; `ASSET_BUCKET=proofstack-assets-<ACCOUNT_ID>-us-east-1`; `UPLOAD_URL_EXPIRY_SECONDS=900`                                    |
| Create   | `ALLOWED_ORIGIN=http://localhost:5173`; `TABLE_NAME=ProofStackEvidence`                                                                                             |
| List     | `ALLOWED_ORIGIN=http://localhost:5173`; `TABLE_NAME=ProofStackEvidence`; `ASSET_BUCKET=proofstack-assets-<ACCOUNT_ID>-us-east-1`; `DOWNLOAD_URL_EXPIRY_SECONDS=900` |
| Get      | `ALLOWED_ORIGIN=http://localhost:5173`; `TABLE_NAME=ProofStackEvidence`; `ASSET_BUCKET=proofstack-assets-<ACCOUNT_ID>-us-east-1`; `DOWNLOAD_URL_EXPIRY_SECONDS=900` |
| Delete   | `ALLOWED_ORIGIN=http://localhost:5173`; `TABLE_NAME=ProofStackEvidence`; `ASSET_BUCKET=proofstack-assets-<ACCOUNT_ID>-us-east-1`                                    |

6. Add exact S3 IAM on `arn:aws:s3:::proofstack-assets-<ACCOUNT_ID>-us-east-1/evidence/demo/*`: presign `s3:PutObject`; list/get `s3:GetObject`; delete `s3:DeleteObject`; create none.
7. Update delete’s table policy to `dynamodb:GetItem` plus `dynamodb:DeleteItem`. DeleteItem is allowed only now because the implemented order is GetItem → exact S3 DeleteObject → DynamoDB DeleteItem. S3 failure retains metadata; complete success is bodyless `204`.
8. Create `/uploads`, then `/uploads/presign`. Add MOCK `OPTIONS` with localhost, `content-type,accept`, and `POST,OPTIONS`. Add proxy `POST` to `proofstack-presign-upload`; use `NONE`, no API key, and allow invoke permission. Redeploy `prod`.
9. Run Lambda Console events only for changed presign/list/get/delete handlers. Use `backend/events/post_uploads_presign.json`, `get_evidence.json`, `get_evidence_demo_id.json`, and `delete_evidence_demo_id.json`. Presign returns `uploadUrl`, `assetKey`, and `expiresIn`; list/get may add temporary `assetUrl`; delete is bodyless `204` only after both deletes.
10. Put this in uncommitted `frontend/.env.local`:

```text
VITE_API_BASE_URL=https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod
```

11. Run `npm --prefix frontend test`, then `npm --prefix frontend run dev` and open `http://localhost:5173`.
12. Verify presign → direct PUT with matching content type → metadata create → newest-first list → get/download → confirmation → exact-object S3-first delete. Keep the evidence bucket private.

Final tree and integrations must be exactly:

| Route                   | Function                     |
| ----------------------- | ---------------------------- |
| `POST /uploads/presign` | `proofstack-presign-upload`  |
| `POST /evidence`        | `proofstack-create-evidence` |
| `GET /evidence`         | `proofstack-list-evidence`   |
| `GET /evidence/{id}`    | `proofstack-get-evidence`    |
| `DELETE /evidence/{id}` | `proofstack-delete-evidence` |

`/workshop` is absent.

## Phase 5 — Build and host the frontend separately

The private bucket stores evidence. A separate bucket exposes only generated frontend assets.

1. Put the invoke base in uncommitted `frontend/.env.production`.
2. Complete **Prompt 3 — Verify frontend integration and build readiness** in [the attendee workbook](attendee-implementation-prompts.internal.md) (`prompt_store/03.txt`). Confirm it changes no AWS configuration.
3. Require these commands to pass:

```powershell
npm --prefix frontend test
npm --prefix frontend run build
```

The build already runs `tsc -b`; do not redundantly run a separate typecheck.

4. Create `proofstack-web-<ACCOUNT_ID>-us-east-1` in S3.
5. Enable static website hosting with index `index.html` and error `index.html`; record the generated website origin without a trailing slash.
6. Disable Block Public Access for this website bucket only and add public read only for build objects:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::proofstack-web-<ACCOUNT_ID>-us-east-1/*"
  }]
}
```

7. Upload the contents of `frontend/dist/` so `index.html` is at bucket root.
8. Replace localhost with `<WEBSITE_ORIGIN>` in all three REST `OPTIONS` Integration Responses, both default Gateway Responses, and all five Lambda `ALLOWED_ORIGIN` values. Preserve exact method lists and `content-type,accept`.
9. Private evidence-bucket CORS may retain both `http://localhost:5173` and `<WEBSITE_ORIGIN>` for GET/HEAD/PUT; keep that bucket private.
10. Redeploy API stage `prod`.
11. From the website, verify full upload/create/list/get/download/confirmed-delete behavior.

## Final IAM and environment summary

| Function | DynamoDB                            | Private S3                  |
| -------- | ----------------------------------- | --------------------------- |
| Presign  | none                                | `PutObject` exact prefix    |
| Create   | `PutItem` exact table               | none                        |
| List     | `Query` exact table                 | `GetObject` exact prefix    |
| Get      | `GetItem` exact table               | `GetObject` exact prefix    |
| Delete   | `GetItem`, `DeleteItem` exact table | `DeleteObject` exact prefix |

Only these Lambda variable names are used: `TABLE_NAME`, `ASSET_BUCKET`, `ALLOWED_ORIGIN`, `UPLOAD_URL_EXPIRY_SECONDS`, and `DOWNLOAD_URL_EXPIRY_SECONDS`.

For detailed Console clicks, complete events, policies, checkpoints, troubleshooting, and architecture matrices, use [the internal workshop runbook](aws-console-workshop.internal.md). For teardown, follow [Console-only cleanup](cleanup.md).
