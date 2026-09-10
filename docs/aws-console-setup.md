# AWS Console setup

Complete every AWS action in the AWS Management Console in `us-east-1`. Use `<account-id>` for the 12-digit AWS account ID and choose globally unique bucket names such as `proofstack-assets-<account-id>-us-east-1` and `proofstack-web-<account-id>-us-east-1`. Record resource names, ARNs, origins, invoke URLs, and deployments outside version control.

Complete the five phases in order.

## 1. Create the Regional REST API shell

### Create the API and resources

1. Open **API Gateway** → **APIs** → **Create API**.
2. Under **REST API**, choose **Build**. Do not choose a private endpoint.
3. Set **API name** to `ProofStackApi` and **Endpoint Type** to **Regional**, then create the API.
4. In **Resources**, create `/uploads`, then create child `/presign` so the complete path is `/uploads/presign`.
5. Create root child `/evidence`, then create child `/{id}`. Name the path parameter exactly `id`.

The final callable resource tree is:

```text
/uploads/presign
/evidence
/evidence/{id}
```

### Create per-resource preflight methods

For each callable resource, create an `OPTIONS` method:

1. Select the resource and choose **Create method** → `OPTIONS`.
2. Set **Authorization** to `NONE` and **API Key Required** to false.
3. Choose integration type **Mock** and create the method.
4. In **Integration request**, ensure a request template for `application/json` returns `{"statusCode": 200}`.
5. In **Method response**, add status `200` and response headers `Access-Control-Allow-Origin`, `Access-Control-Allow-Headers`, and `Access-Control-Allow-Methods`.
6. In **Integration response** for `200`, map those headers to quoted static values.

Use these exact values initially:

| Resource           | `Access-Control-Allow-Origin` | `Access-Control-Allow-Headers` | `Access-Control-Allow-Methods` |
| ------------------ | ----------------------------- | ------------------------------ | ------------------------------ |
| `/uploads/presign` | `http://localhost:5173`       | `content-type,accept`          | `POST,OPTIONS`                 |
| `/evidence`        | `http://localhost:5173`       | `content-type,accept`          | `GET,POST,OPTIONS`             |
| `/evidence/{id}`   | `http://localhost:5173`       | `content-type,accept`          | `GET,DELETE,OPTIONS`           |

Enter static integration-response values with the quoting required by the API Gateway Console, for example `'http://localhost:5173'`.

### Configure gateway-generated error CORS and deploy

1. Open **Gateway Responses**.
2. Edit `DEFAULT_4XX` and `DEFAULT_5XX`.
3. Add response parameters:
   - `gatewayresponse.header.Access-Control-Allow-Origin` = `'http://localhost:5173'`
   - `gatewayresponse.header.Access-Control-Allow-Headers` = `'content-type,accept'`
   - `gatewayresponse.header.Access-Control-Allow-Methods` = `'GET,POST,DELETE,OPTIONS'`
4. Return to **Resources**, choose **Deploy API**, create stage `prod`, and deploy.
5. Record the invoke base: `https://<api-id>.execute-api.us-east-1.amazonaws.com/prod`.
6. Confirm preflight responses from each resource and confirm the stage is named exactly `prod`.

REST API configuration changes do not reach callers until you explicitly choose **Deploy API** and target `prod`.

## 2. Create five Python Lambdas and connect business methods

For each function:

1. Open **Lambda** → **Functions** → **Create function** → **Author from scratch**.
2. Use Python 3.12, `x86_64`, and a separate role with basic Lambda logging permissions.
3. In **Code**, replace `lambda_function.py` with the matching repository source and choose **Deploy**. Keep the handler as `lambda_function.lambda_handler`.
4. Set timeout to 10 seconds and memory to 256 MB.
5. Set `ALLOWED_ORIGIN=http://localhost:5173` under **Configuration** → **Environment variables**.

| Function name                | REST API business method |
| ---------------------------- | ------------------------ |
| `proofstack-presign-upload`  | `POST /uploads/presign`  |
| `proofstack-create-evidence` | `POST /evidence`         |
| `proofstack-list-evidence`   | `GET /evidence`          |
| `proofstack-get-evidence`    | `GET /evidence/{id}`     |
| `proofstack-delete-evidence` | `DELETE /evidence/{id}`  |

For each row:

1. Open `ProofStackApi` → **Resources**, select the exact resource, and choose **Create method** with the listed verb.
2. Set **Authorization** to `NONE` and **API Key Required** to false.
3. Choose integration type **Lambda function**, enable **Lambda proxy integration**, select the function in `us-east-1`, and allow API Gateway to add invoke permission.
4. Save the method. Do not add request or response mapping templates to a proxy integration.

Item events use `pathParameters.id`. After all five integrations are saved, choose **Deploy API** and redeploy stage `prod`. Confirm the API appears under each Lambda's triggers and the frontend invoke base still ends in `/prod`.

Run the matching event described in [Lambda Console testing](lambda-console-testing.md). At this phase, future resource variables are intentionally absent. A handler that requires one returns `500` with error code `CONFIGURATION_ERROR`. If all variables required by an unfinished operation have been added, that operation returns `501` with error code `NOT_IMPLEMENTED`.

## 3. Create DynamoDB and activate metadata operations

1. Open **DynamoDB** → **Tables** → **Create table**.
2. Set table name to `ProofStackEvidence`, partition key to `PK` of type **String**, and sort key to `SK` of type **String**.
3. Keep on-demand capacity, create the table, and record `arn:aws:dynamodb:us-east-1:<account-id>:table/ProofStackEvidence`.
4. Set `TABLE_NAME=ProofStackEvidence` on create, list, get, and delete.
5. Add inline policies scoped to that exact table ARN:

| Function                     | DynamoDB actions                          |
| ---------------------------- | ----------------------------------------- |
| `proofstack-create-evidence` | `dynamodb:PutItem`                        |
| `proofstack-list-evidence`   | `dynamodb:Query`                          |
| `proofstack-get-evidence`    | `dynamodb:GetItem`                        |
| `proofstack-delete-evidence` | `dynamodb:GetItem`, `dynamodb:DeleteItem` |
| `proofstack-presign-upload`  | none                                      |

Items use `PK = USER#demo` and `SK = EVIDENCE#<id>`. Generate `id` as a compact fixed-width UTC timestamp followed by a UUID segment, such as `20250102T030405123456Z-a1b2c3d4`. Store file references in `assetKey`.

List uses a DynamoDB Query with `PK = USER#demo`, the `EVIDENCE#` sort-key prefix, and descending sort-key order. It never uses Scan and returns all items without pagination. Do not expose `PK` or `SK`.

Keep basic logging permissions limited to `logs:CreateLogGroup`, `logs:CreateLogStream`, and `logs:PutLogEvents`. Test data through ProofStack requests, not the DynamoDB item editor.

## 4. Create the private evidence bucket and activate signed file operations

1. Open **S3** → **Buckets** → **Create bucket**. Enter the recorded asset bucket name and select `us-east-1`.
2. Keep all four **Block Public Access** settings enabled. Keep ACLs disabled, enable default encryption, and create the bucket.
3. On **Permissions**, configure CORS for local browser PUT and GET:

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

4. Add environment variables:

| Function                     | Phase-4 variables                                                |
| ---------------------------- | ---------------------------------------------------------------- |
| `proofstack-presign-upload`  | `ASSET_BUCKET=<asset-bucket>`, `UPLOAD_URL_EXPIRY_SECONDS=900`   |
| `proofstack-create-evidence` | none                                                             |
| `proofstack-list-evidence`   | `ASSET_BUCKET=<asset-bucket>`, `DOWNLOAD_URL_EXPIRY_SECONDS=900` |
| `proofstack-get-evidence`    | `ASSET_BUCKET=<asset-bucket>`, `DOWNLOAD_URL_EXPIRY_SECONDS=900` |
| `proofstack-delete-evidence` | `ASSET_BUCKET=<asset-bucket>`                                    |

5. Add inline S3 policies. Scope every Resource to `arn:aws:s3:::<asset-bucket>/evidence/demo/*`:

| Function                     | S3 actions        | Use                                            |
| ---------------------------- | ----------------- | ---------------------------------------------- |
| `proofstack-presign-upload`  | `s3:PutObject`    | Sign short-lived browser PUT requests.         |
| `proofstack-create-evidence` | none              | Uses `dynamodb:PutItem` only.                  |
| `proofstack-list-evidence`   | `s3:GetObject`    | Sign short-lived GET URLs for list items.      |
| `proofstack-get-evidence`    | `s3:GetObject`    | Sign a short-lived GET URL for one item.       |
| `proofstack-delete-evidence` | `s3:DeleteObject` | Delete the exact asset selected from metadata. |

Presign accepts:

```json
{"fileName":"receipt.pdf","contentType":"application/pdf"}
```

It returns `uploadUrl`, `assetKey`, and `expiresIn`; `assetKey` starts with `evidence/demo/`. Bind the signed PUT to the submitted content type. List and get may return temporary `assetUrl` values, which must not be stored or logged.

Delete uses GetItem to locate `assetKey`, deletes that exact S3 object first, and calls DeleteItem only after S3 succeeds. Return an empty `204` only after both operations succeed.

## 5. Build React and deploy the public website bucket

1. Set `VITE_API_BASE_URL` in an uncommitted production environment file to `https://<api-id>.execute-api.us-east-1.amazonaws.com/prod` without a trailing slash.
2. Run the local frontend tests, type checks, and production build.
3. In **S3**, create the recorded website bucket in `us-east-1`. This bucket is separate from the private evidence bucket.
4. Enable **Static website hosting** and set both index and error documents to `index.html`. Record the exact website origin.
5. Disable Block Public Access for this website bucket only. Add a bucket policy that grants public `s3:GetObject` only on `arn:aws:s3:::<website-bucket>/*`.
6. Upload the contents of `frontend/dist/` so `index.html` is at the bucket root. Do not upload source, environment files, or credentials.
7. For each REST `OPTIONS` integration response, replace `http://localhost:5173` with the exact website origin. Preserve the resource's exact allow-method list and `content-type,accept` headers.
8. In Gateway Responses `DEFAULT_4XX` and `DEFAULT_5XX`, replace the local origin with the exact website origin and preserve the other CORS values.
9. Update `ALLOWED_ORIGIN` on all five Lambdas to the exact website origin used by deployed responses.
10. In the private asset bucket CORS rule, add the exact website origin alongside localhost; preserve `GET`, `HEAD`, and `PUT`. Keep Block Public Access enabled.
11. In API Gateway, choose **Deploy API** and redeploy stage `prod` so all REST CORS changes are live.
12. Open the website and exercise presign/PUT, create, newest-first list, get/download, and delete. Public access remains limited to the frontend bucket.
