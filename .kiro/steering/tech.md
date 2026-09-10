---
inclusion: always
---

# Technology

Use this stack without substitution:

- React, Vite, and TypeScript for the browser application.
- Python for five AWS Lambda handlers.
- Amazon API Gateway Regional REST API with Lambda proxy integration and named stage `prod`.
- Amazon DynamoDB with string keys `PK` and `SK`.
- One private S3 bucket for evidence files.
- One separate public S3 bucket for the built frontend.

## REST API rules

- Create REST resources `/uploads/presign`, `/evidence`, and `/evidence/{id}`. Connect the five business methods with Lambda proxy integration.
- Set **Authorization** to `NONE` and **API Key Required** to false on business methods and `OPTIONS`; do not implement authentication or API keys.
- REST proxy events use top-level `httpMethod`, `path`, and `resource`; item events use `pathParameters.id`; Console events use `requestContext.stage = "prod"`.
- Add per-resource `OPTIONS` methods with `MOCK` integrations. Initially allow `http://localhost:5173`, headers `content-type,accept`, and exact method lists `POST,OPTIONS` for `/uploads/presign`, `GET,POST,OPTIONS` for `/evidence`, and `GET,DELETE,OPTIONS` for `/evidence/{id}`.
- Add CORS headers to Gateway Responses `DEFAULT_4XX` and `DEFAULT_5XX`.
- Explicitly deploy and redeploy API changes to `prod`. Use invoke base `https://<api-id>.execute-api.<region>.amazonaws.com/prod`.
- During phase 5 frontend publication, replace localhost in final REST `OPTIONS`, Gateway Responses, and all five Lambda `ALLOWED_ORIGIN` values with the website origin, then redeploy. Private S3 CORS may retain both origins.

## Technical rules

- Use `USER#demo` for every data operation; do not implement authentication.
- Keep Lambda files standalone and directly copyable as `lambda_function.py` with handler `lambda_handler`.
- Lambda code may use the Python standard library and the AWS SDK available in the runtime; avoid runtime package dependencies unless essential.
- Use only `TABLE_NAME`, `ASSET_BUCKET`, `ALLOWED_ORIGIN`, `UPLOAD_URL_EXPIRY_SECONDS`, and `DOWNLOAD_URL_EXPIRY_SECONDS` for Lambda deployment values.
- Use `assetKey`. S3 keys start with `evidence/demo/`; list/get responses may add temporary `assetUrl` values after signed downloads are enabled.
- Generate `id` as a compact fixed-width UTC timestamp plus UUID segment and store `SK = EVIDENCE#<id>`.
- List with DynamoDB Query, never Scan, in descending sort-key order. Do not paginate.
- Return JSON errors as `{"error":{"code":"...","message":"..."}}`; only a successful `204` delete has no body.
- Use short-lived presigned PUT and GET URLs. Never place AWS credentials in frontend code.
- Apply exact least privilege: presign `s3:PutObject`; create `dynamodb:PutItem`; list `dynamodb:Query` and, after signed downloads are enabled, `s3:GetObject`; get `dynamodb:GetItem` and `s3:GetObject`; delete `dynamodb:GetItem`, `s3:DeleteObject`, then `dynamodb:DeleteItem`.
- Scope DynamoDB permissions to the exact table and S3 permissions to `arn:aws:s3:::<asset-bucket>/evidence/demo/*`.
