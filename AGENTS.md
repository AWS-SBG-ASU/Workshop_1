# ProofStack Repository Guidance

ProofStack is a personal evidence application for uploading private files, recording evidence metadata, browsing saved evidence, downloading files through temporary links, and deleting records with their files.

## Required architecture

- Frontend: React, Vite, and TypeScript in `frontend/`.
- API: Amazon API Gateway Regional REST API with Lambda proxy integration and named stage `prod`.
- Compute: five standalone Python Lambda handlers in `backend/`.
- Data: one DynamoDB table with string keys `PK` and `SK`.
- Storage: one private S3 evidence bucket and one separate public S3 frontend bucket.
- Identity: use `USER#demo` for every data operation; do not add authentication.

## Delivery rules

- Provision and configure AWS resources only in the AWS Management Console.
- Do not use AWS CLI, SAM, CDK, Terraform, OpenTofu, Pulumi, Serverless Framework, or other infrastructure-as-code tooling.
- Keep every Lambda source file self-contained, with `lambda_handler` as the entry point and no project-local runtime imports, so its contents can be copied directly into `lambda_function.py`.
- Follow test-driven development. After every Lambda change, run a Lambda Console test with an API Gateway REST API Lambda proxy event and record the expected result.
- REST proxy events use top-level `httpMethod`, `path`, and `resource`; item events use `pathParameters.id`; every Console event uses `requestContext.stage = "prod"`.
- Use only these Lambda environment variable names: `TABLE_NAME`, `ASSET_BUCKET`, `ALLOWED_ORIGIN`, `UPLOAD_URL_EXPIRY_SECONDS`, and `DOWNLOAD_URL_EXPIRY_SECONDS`.
- Keep credentials, resource names, local environment values, and generated presigned URLs out of source and logs.
- Apply least-privilege IAM permissions scoped to the exact DynamoDB table and the private S3 prefix `evidence/demo/*`.

## API and data contract

Create these REST resources and business methods:

- `POST /uploads/presign`
- `POST /evidence`
- `GET /evidence`
- `GET /evidence/{id}`
- `DELETE /evidence/{id}`

Enable Lambda proxy integration for every business method. Set **Authorization** to `NONE` and **API Key Required** to false for every business method and every `OPTIONS` method; ProofStack has no authentication or API-key requirement.

Create an `OPTIONS` method with a `MOCK` integration on `/uploads/presign`, `/evidence`, and `/evidence/{id}`. Initially return `Access-Control-Allow-Origin: http://localhost:5173`, `Access-Control-Allow-Headers: content-type,accept`, and exact per-resource method lists: `POST,OPTIONS`; `GET,POST,OPTIONS`; and `GET,DELETE,OPTIONS`, respectively. Add the same local-origin CORS headers to Gateway Responses `DEFAULT_4XX` and `DEFAULT_5XX`.

Parameterized events use `pathParameters.id`. Presign input is `fileName` and `contentType`; its response contains `uploadUrl`, `assetKey`, and `expiresIn`. Evidence records use `assetKey`, and list/get responses may include a temporary `assetUrl` after signed downloads are enabled.

Every item uses `PK = USER#demo` and `SK = EVIDENCE#<id>`. The `id` starts with a compact UTC timestamp and ends with a UUID segment so a descending DynamoDB Query returns newest records first. Asset keys start with `evidence/demo/`. List uses Query, never Scan, and does not paginate.

JSON errors use `{"error":{"code":"...","message":"..."}}`; the only bodyless response is a successful `204` delete. Delete reads the item, deletes its exact S3 asset, and only then deletes the DynamoDB item.

## Required build order

Complete these phases in order: (1) deploy a Regional REST API foundation with temporary `GET` and `OPTIONS` MOCK methods on `/workshop`, local CORS, and Gateway Responses; (2) create only `proofstack-list-evidence`, switch `GET /workshop` to Lambda proxy, and redeploy/test; (3) create `ProofStackEvidence`, evolve list, create the create/get/delete metadata Lambdas, add `/evidence` and `/evidence/{id}` with their final methods and `OPTIONS`, keep delete incomplete so metadata remains, remove `/workshop`, and redeploy; (4) create private S3, create presign, enhance list/get/delete, add `/uploads/presign`, complete exact IAM and the local lifecycle, and redeploy; (5) build React, publish it to the separate public S3 bucket, perform the final origin cutover, and redeploy. The final result remains exactly five standalone Lambdas and the five stable business routes.

Explicitly deploy the REST API to `prod` after initial API setup and redeploy `prod` after every resource, method, integration, CORS, or Gateway Response change. The invoke base is `https://<api-id>.execute-api.<region>.amazonaws.com/prod`. Set `ALLOWED_ORIGIN=http://localhost:5173` as each Lambda is introduced. In phase 5, replace localhost in final REST `OPTIONS`, `DEFAULT_4XX`, `DEFAULT_5XX`, and every Lambda `ALLOWED_ORIGIN` with the exact website origin, then redeploy `prod`. The private evidence-bucket CORS rule may retain both localhost and the website origin.

## Source of truth

Read `.kiro/steering/` before changing code. Use `.kiro/specs/proofstack/requirements.md`, `design.md`, and `tasks.md` as the product contract, architecture, and required delivery sequence.
