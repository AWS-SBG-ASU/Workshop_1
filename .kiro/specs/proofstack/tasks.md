# ProofStack Build Tasks

Complete phases in order. Do not provision a later phase before its predecessor is verified. Use test-driven development for every handler and run a Lambda Console API Gateway REST API Lambda proxy event for stage `prod` after every handler change.

## 1. Provision the Regional REST API shell

- [ ] 1.1 In the AWS Management Console, create an API Gateway REST API named `ProofStackApi` with endpoint type **Regional**.
- [ ] 1.2 Create resources `/uploads/presign`, `/evidence`, and `/evidence/{id}`; name the path parameter exactly `id`.
- [ ] 1.3 On each resource, create an `OPTIONS` method with **Authorization** `NONE`, **API Key Required** false, and a `MOCK` integration that returns status `200`.
- [ ] 1.4 Configure `OPTIONS` method and integration responses with `Access-Control-Allow-Origin: http://localhost:5173`, `Access-Control-Allow-Headers: content-type,accept`, and exact allow-method lists: `/uploads/presign` `POST,OPTIONS`; `/evidence` `GET,POST,OPTIONS`; `/evidence/{id}` `GET,DELETE,OPTIONS`.
- [ ] 1.5 Configure Gateway Responses `DEFAULT_4XX` and `DEFAULT_5XX` with local-origin CORS headers.
- [ ] 1.6 Choose **Deploy API**, create named stage `prod`, and record `https://<api-id>.execute-api.<region>.amazonaws.com/prod` as the frontend invoke base.
- [ ] 1.7 Confirm resources, `OPTIONS` behavior, Gateway Responses, and the `prod` deployment without using AWS CLI or infrastructure-as-code tooling.

## 2. Create five Lambdas and attach business methods

- [ ] 2.1 Write failing local contract tests using REST proxy events with top-level `httpMethod`, `path`, `resource`, and `requestContext.stage = "prod"`; item events also use `pathParameters.id`.
- [ ] 2.2 Create standalone `presign_upload`, `create_evidence`, `list_evidence`, `get_evidence`, and `delete_evidence` Python handler files; each must be directly copyable to `lambda_function.py`.
- [ ] 2.3 In the Lambda Console, create five Python functions with `lambda_handler` as the entry point and separate execution roles.
- [ ] 2.4 Set `ALLOWED_ORIGIN=http://localhost:5173` on all five functions so scaffold responses include the local origin.
- [ ] 2.5 Create these REST business methods. For each, set **Authorization** `NONE`, **API Key Required** false, enable Lambda proxy integration, and select the matching function:
  - `POST /uploads/presign` -> `presign_upload`
  - `POST /evidence` -> `create_evidence`
  - `GET /evidence` -> `list_evidence`
  - `GET /evidence/{id}` -> `get_evidence`
  - `DELETE /evidence/{id}` -> `delete_evidence`
- [ ] 2.6 Ensure parameterized events use `pathParameters.id` and all business methods have API Gateway permission to invoke their Lambdas.
- [ ] 2.7 Explicitly redeploy the API to `prod` after all integrations are attached.
- [ ] 2.8 Run local and Lambda Console tests. Before future resource environment variables exist, affected handlers shall return controlled `500` errors with code `CONFIGURATION_ERROR`. If every variable required by an unfinished operation is present, its scaffold shall return `501` with code `NOT_IMPLEMENTED`.

## 3. Provision DynamoDB and activate metadata operations

- [ ] 3.1 In the DynamoDB Console, create the metadata table with string partition key `PK` and string sort key `SK`.
- [ ] 3.2 Set `TABLE_NAME` on create, list, get, and delete.
- [ ] 3.3 Scope table permissions to the exact table ARN: create `dynamodb:PutItem`; list `dynamodb:Query`; get `dynamodb:GetItem`; delete `dynamodb:GetItem` and `dynamodb:DeleteItem`.
- [ ] 3.4 Drive create from failing tests: generate a compact fixed-width UTC timestamp plus UUID segment for `id`; write `PK = USER#demo`, `SK = EVIDENCE#<id>`, validated metadata using `assetKey`, and `createdAt`.
- [ ] 3.5 Drive list from failing tests: use Query, never Scan, with `PK = USER#demo`, the `EVIDENCE#` sort-key prefix, and descending sort-key order. Return all records newest first with no pagination or internal keys.
- [ ] 3.6 Drive get from failing tests: validate `pathParameters.id`, use GetItem, omit internal keys, and return `404` when absent.
- [ ] 3.7 Drive delete metadata lookup from failing tests. Retain the item until phase-4 S3 deletion succeeds.
- [ ] 3.8 After every handler change, pass local tests and run the matching Lambda Console REST proxy event for `prod`.

## 4. Provision private S3 and activate signed PUT/GET and delete

- [ ] 4.1 In the S3 Console, create the private evidence bucket with all Block Public Access settings enabled.
- [ ] 4.2 Configure bucket CORS for browser `PUT`, `GET`, and `HEAD` from `http://localhost:5173`; do not make evidence objects public.
- [ ] 4.3 Set phase-4 variables:
  - presign: `ASSET_BUCKET`, `UPLOAD_URL_EXPIRY_SECONDS`
  - list: `ASSET_BUCKET`, `DOWNLOAD_URL_EXPIRY_SECONDS`
  - get: `ASSET_BUCKET`, `DOWNLOAD_URL_EXPIRY_SECONDS`
  - delete: `ASSET_BUCKET`
- [ ] 4.4 Scope S3 permissions to `arn:aws:s3:::<asset-bucket>/evidence/demo/*`: presign `s3:PutObject`; list `s3:GetObject`; get `s3:GetObject`; delete `s3:DeleteObject`. Create receives no S3 permission and keeps only `dynamodb:PutItem`.
- [ ] 4.5 Drive presign from failing tests: accept `fileName` and `contentType`; return `uploadUrl`, a unique `assetKey` under `evidence/demo/`, and `expiresIn`; bind the PUT signature to the content type.
- [ ] 4.6 Drive signed download behavior from failing tests. List and get may add temporary `assetUrl` values generated from each record's `assetKey`; never store or log those URLs.
- [ ] 4.7 Drive delete from failing tests: get the record, delete its exact S3 `assetKey` first, call DeleteItem only after S3 succeeds, and return an empty `204`.
- [ ] 4.8 After every handler change, pass local tests and run the matching Lambda Console REST proxy event for `prod`.
- [ ] 4.9 Verify presign, PUT, metadata create, newest-first list, get/download, and delete through the `/prod` API while the evidence bucket remains private.

## 5. Build React and deploy to public S3

- [ ] 5.1 Complete the React/Vite/TypeScript UI for upload-and-create, list, detail/download, delete confirmation, loading, empty, success, validation, not-found, and dependency-failure states.
- [ ] 5.2 Configure `VITE_API_BASE_URL` with the REST API invoke base ending in `/prod`, without a trailing slash, and keep AWS credentials, bucket names, and generated URLs out of frontend source.
- [ ] 5.3 Write failing frontend tests first, implement the typed API client and user flows, and pass tests and type checks.
- [ ] 5.4 Run the Vite production build.
- [ ] 5.5 In the S3 Console, create the separate frontend bucket, configure static website hosting, and grant public read only to built website objects.
- [ ] 5.6 Upload the production build output through the S3 Console and record the exact website origin.
- [ ] 5.7 Replace localhost with that website origin in every REST `OPTIONS` integration response and Gateway Responses `DEFAULT_4XX` and `DEFAULT_5XX`. Update all five Lambdas' `ALLOWED_ORIGIN` to the same website origin.
- [ ] 5.8 Add the website origin alongside `http://localhost:5173` in private evidence-bucket CORS; preserve `GET`, `HEAD`, and `PUT` and keep Block Public Access enabled.
- [ ] 5.9 Explicitly redeploy the REST API to `prod`, then complete an end-to-end check of all five API routes from the deployed frontend.
