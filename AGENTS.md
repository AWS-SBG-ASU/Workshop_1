# ProofStack Repository Guidance

ProofStack is a personal evidence application for uploading private files, recording evidence metadata, browsing saved evidence, downloading files through temporary links, and deleting records with their files.

## Required architecture

- Frontend: React, Vite, and TypeScript in `frontend/`.
- API: Amazon API Gateway HTTP API with payload format 2.0.
- Compute: five standalone Python Lambda handlers in `backend/`.
- Data: one DynamoDB table with string keys `PK` and `SK`.
- Storage: one private S3 evidence bucket and one separate public S3 frontend bucket.
- Identity: use `USER#demo` for every data operation; do not add authentication.

## Delivery rules

- Provision and configure AWS resources only in the AWS Management Console.
- Do not use AWS CLI, SAM, CDK, Terraform, OpenTofu, Pulumi, Serverless Framework, or other infrastructure-as-code tooling.
- Keep every Lambda source file self-contained, with `lambda_handler` as the entry point and no project-local runtime imports, so its contents can be copied directly into `lambda_function.py`.
- Follow test-driven development. After every Lambda change, run a Lambda Console test with an API Gateway HTTP API payload format 2.0 event and record the expected result.
- Use only these Lambda environment variable names: `TABLE_NAME`, `ASSET_BUCKET`, `ALLOWED_ORIGIN`, `UPLOAD_URL_EXPIRY_SECONDS`, and `DOWNLOAD_URL_EXPIRY_SECONDS`.
- Keep credentials, resource names, local environment values, and generated presigned URLs out of source and logs.
- Apply least-privilege IAM permissions scoped to the exact DynamoDB table and the private S3 prefix `evidence/demo/*`.

## API and data contract

- `POST /uploads/presign`
- `POST /evidence`
- `GET /evidence`
- `GET /evidence/{id}`
- `DELETE /evidence/{id}`

Parameterized events use `pathParameters.id`. Presign input is `fileName` and `contentType`; its response contains `uploadUrl`, `assetKey`, and `expiresIn`. Evidence records use `assetKey`, and list/get responses may include a temporary `assetUrl` after signed downloads are enabled.

Every item uses `PK = USER#demo` and `SK = EVIDENCE#<id>`. The `id` starts with a compact UTC timestamp and ends with a UUID segment so a descending DynamoDB Query returns newest records first. Asset keys start with `evidence/demo/`. List uses Query, never Scan, and does not paginate.

JSON errors use `{"error":{"code":"...","message":"..."}}`; the only bodyless response is a successful `204` delete. Delete reads the item, deletes its exact S3 asset, and only then deletes the DynamoDB item.

## Required build order

Complete these phases in order: API Gateway shell; five Lambdas and routes; DynamoDB metadata; private S3 signed PUT/GET and delete; React build and public S3 hosting. Configure API Gateway CORS for `http://localhost:5173` in phase 1, set Lambda `ALLOWED_ORIGIN` in phase 2, and add the website origin to API Gateway and S3 CORS while updating `ALLOWED_ORIGIN` in phase 5.

## Source of truth

Read `.kiro/steering/` before changing code. Use `.kiro/specs/proofstack/requirements.md`, `design.md`, and `tasks.md` as the product contract, architecture, and required delivery sequence.