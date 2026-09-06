---
inclusion: always
---

# Technology

Use this stack without substitution:

- React, Vite, and TypeScript for the browser application.
- Python for five AWS Lambda handlers.
- Amazon API Gateway HTTP API with payload format 2.0.
- Amazon DynamoDB with string keys `PK` and `SK`.
- One private S3 bucket for evidence files.
- One separate public S3 bucket for the built frontend.

## Technical rules

- Use `USER#demo` for every data operation; do not implement authentication.
- Keep Lambda files standalone and directly copyable as `lambda_function.py` with handler `lambda_handler`.
- Lambda code may use the Python standard library and the AWS SDK available in the runtime; avoid runtime package dependencies unless essential.
- Use only `TABLE_NAME`, `ASSET_BUCKET`, `ALLOWED_ORIGIN`, `UPLOAD_URL_EXPIRY_SECONDS`, and `DOWNLOAD_URL_EXPIRY_SECONDS` for Lambda deployment values.
- Use `assetKey`. S3 keys start with `evidence/demo/`; phase-4 list/get responses may add temporary `assetUrl` values.
- Generate `id` as a compact fixed-width UTC timestamp plus UUID segment and store `SK = EVIDENCE#<id>`.
- List with DynamoDB Query, never Scan, in descending sort-key order. Do not paginate.
- Return JSON errors as `{"error":{"code":"...","message":"..."}}`; only a successful `204` delete has no body.
- Use short-lived presigned PUT and GET URLs. Never place AWS credentials in frontend code.
- Apply exact least privilege: presign `s3:PutObject`; create `dynamodb:PutItem`; list `dynamodb:Query` and phase-4 `s3:GetObject`; get `dynamodb:GetItem` and `s3:GetObject`; delete `dynamodb:GetItem`, `s3:DeleteObject`, then `dynamodb:DeleteItem`.
- Scope DynamoDB permissions to the exact table and S3 permissions to `arn:aws:s3:::<asset-bucket>/evidence/demo/*`.