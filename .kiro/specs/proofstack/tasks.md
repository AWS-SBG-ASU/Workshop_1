# ProofStack Build Tasks

Complete phases in order. Do not provision a later service before its predecessor is verified. Use test-driven development for every handler and run a Lambda Console API Gateway REST API Lambda proxy event with `requestContext.stage = "prod"` after every handler change.

## 1. Establish API Gateway with a disposable workshop route

- [ ] 1.1 In the AWS Management Console, create an API Gateway REST API named `ProofStackApi` with endpoint type **Regional**.
- [ ] 1.2 Create only the temporary `/workshop` resource. Do not create `/uploads/presign`, `/evidence`, or `/evidence/{id}` yet.
- [ ] 1.3 Create `GET /workshop` with **Authorization** `NONE`, **API Key Required** false, and a `MOCK` integration returning a dependency-free `200` workshop response.
- [ ] 1.4 Create `OPTIONS /workshop` with **Authorization** `NONE`, **API Key Required** false, and a `MOCK` integration returning status `200`.
- [ ] 1.5 Configure `/workshop` CORS with `Access-Control-Allow-Origin: http://localhost:5173`, `Access-Control-Allow-Headers: content-type,accept`, and `Access-Control-Allow-Methods: GET,OPTIONS`.
- [ ] 1.6 Configure Gateway Responses `DEFAULT_4XX` and `DEFAULT_5XX` with local-origin CORS headers so gateway-generated errors are browser-readable.
- [ ] 1.7 Choose **Deploy API**, create the named stage `prod`, and record `https://<api-id>.execute-api.<region>.amazonaws.com/prod` as the invoke base.
- [ ] 1.8 Verify the deployed `GET` and `OPTIONS` behavior for `/workshop` and confirm that no final service route exists yet.

## 2. Introduce the first Lambda through the workshop route

- [ ] 2.1 Write a failing local contract test for a dependency-free `GET /workshop` REST proxy event with top-level `httpMethod`, `path`, `resource`, and `requestContext.stage = "prod"`.
- [ ] 2.2 Implement only the standalone list handler source used by `proofstack-list-evidence`; at this phase it shall return a safe temporary workshop response without DynamoDB, S3, or project-local runtime dependencies.
- [ ] 2.3 In the Lambda Console, create only the Python function `proofstack-list-evidence` with `lambda_handler` as the entry point and a dedicated execution role.
- [ ] 2.4 Set `ALLOWED_ORIGIN=http://localhost:5173` and copy the standalone handler into the Lambda editor as `lambda_function.py`.
- [ ] 2.5 Run the matching Lambda Console REST proxy test event for `GET /workshop` and record the expected `200` response and local CORS origin.
- [ ] 2.6 Replace the `GET /workshop` MOCK integration with Lambda proxy integration targeting `proofstack-list-evidence`; retain **Authorization** `NONE` and **API Key Required** false.
- [ ] 2.7 Grant API Gateway permission to invoke the Lambda, explicitly redeploy to `prod`, and verify `GET /workshop` through the deployed invoke URL.

## 3. Add DynamoDB and the metadata API

- [ ] 3.1 In the DynamoDB Console, create `ProofStackEvidence` with string partition key `PK` and string sort key `SK`.
- [ ] 3.2 Write failing metadata tests using REST proxy events. Item events shall use `pathParameters.id`; every event shall include top-level `httpMethod`, `path`, and `resource` plus `requestContext.stage = "prod"`.
- [ ] 3.3 Evolve `proofstack-list-evidence` to Query, never Scan, for `PK = USER#demo` and the `EVIDENCE#` prefix in descending sort-key order, with no pagination or internal keys.
- [ ] 3.4 Implement standalone create, get, and delete metadata handlers and create their Lambda Console functions with dedicated execution roles. Do not create the presign Lambda yet.
- [ ] 3.5 Set `ALLOWED_ORIGIN=http://localhost:5173` on the new handlers and set `TABLE_NAME=ProofStackEvidence` on list, create, get, and delete.
- [ ] 3.6 Apply exact DynamoDB permissions against the exact table ARN: list `dynamodb:Query`; create `dynamodb:PutItem`; get `dynamodb:GetItem`; delete `dynamodb:GetItem` only during this incomplete-delete phase.
- [ ] 3.7 Implement create with `PK = USER#demo`, `SK = EVIDENCE#<id>`, validated `assetKey` metadata, `createdAt`, and a compact fixed-width UTC timestamp plus UUID segment for `id`.
- [ ] 3.8 Implement get with `pathParameters.id`, GetItem, omission of internal keys, and `404` for a missing record.
- [ ] 3.9 Implement delete metadata lookup and not-found behavior, but do not delete metadata yet. Return controlled incomplete-operation behavior and retain the item until phase-4 S3-first deletion is available.
- [ ] 3.10 In API Gateway, create `/evidence` and `/evidence/{id}` with path parameter exactly `id`.
- [ ] 3.11 Add `POST /evidence`, `GET /evidence`, `GET /evidence/{id}`, and `DELETE /evidence/{id}`. Set **Authorization** `NONE`, **API Key Required** false, and Lambda proxy integration to the matching function on every method.
- [ ] 3.12 Add MOCK `OPTIONS` methods with **Authorization** `NONE` and **API Key Required** false. Use origin `http://localhost:5173`, headers `content-type,accept`, and exact method lists `/evidence` `GET,POST,OPTIONS` and `/evidence/{id}` `GET,DELETE,OPTIONS`.
- [ ] 3.13 Run focused local tests and the matching Lambda Console REST proxy test after every handler change, including success, malformed input, missing configuration, not-found, and dependency-failure cases.
- [ ] 3.14 Remove the temporary `/workshop` resource before completing this phase. Confirm it is absent and no final route depends on it.
- [ ] 3.15 Explicitly redeploy to `prod`, then verify metadata create, newest-first list, get, not-found, and intentionally incomplete delete through the deployed API.

## 4. Add private S3 and complete the five-route service

- [ ] 4.1 In the S3 Console, create the private evidence bucket with all Block Public Access settings enabled.
- [ ] 4.2 Configure private-bucket CORS for browser `PUT`, `GET`, and `HEAD` from `http://localhost:5173`; do not make evidence objects public.
- [ ] 4.3 Write failing tests for presigned upload, signed downloads, and S3-first delete behavior.
- [ ] 4.4 Implement the standalone presign handler and create `proofstack-presign-upload` in the Lambda Console, bringing the final total to five standalone Lambdas. Set `ALLOWED_ORIGIN`, `ASSET_BUCKET`, and `UPLOAD_URL_EXPIRY_SECONDS`.
- [ ] 4.5 Set `ASSET_BUCKET` and `DOWNLOAD_URL_EXPIRY_SECONDS` on list and get; set `ASSET_BUCKET` on delete. Use only the approved Lambda environment variable names.
- [ ] 4.6 Scope S3 permissions to `arn:aws:s3:::<asset-bucket>/evidence/demo/*`: presign `s3:PutObject`; list `s3:GetObject`; get `s3:GetObject`; delete `s3:DeleteObject`. Create receives no S3 permission.
- [ ] 4.7 Add `dynamodb:DeleteItem` on the exact table ARN to delete. Its final permissions shall be `dynamodb:GetItem`, then `s3:DeleteObject`, then `dynamodb:DeleteItem` in execution order.
- [ ] 4.8 Implement presign to accept `fileName` and `contentType`, bind the signed PUT to the content type, and return `uploadUrl`, a unique `assetKey` under `evidence/demo/`, and `expiresIn`.
- [ ] 4.9 Enhance list and get to generate optional short-lived `assetUrl` values from each record's `assetKey`; never store or log temporary URLs.
- [ ] 4.10 Complete delete so it gets the record, deletes its exact S3 `assetKey` first, calls DeleteItem only after S3 succeeds, retains metadata on S3 failure, and returns an empty `204` on success.
- [ ] 4.11 Only now create `/uploads/presign`, add `POST` with Lambda proxy integration, **Authorization** `NONE`, and **API Key Required** false.
- [ ] 4.12 Add its MOCK `OPTIONS` method with **Authorization** `NONE`, **API Key Required** false, origin `http://localhost:5173`, headers `content-type,accept`, and exact methods `POST,OPTIONS`.
- [ ] 4.13 Run focused local tests and matching Lambda Console REST proxy tests after every changed handler.
- [ ] 4.14 Explicitly redeploy to `prod`, then verify the full local lifecycle: presign, browser PUT, metadata create, newest-first list, get/download, and S3-first delete while the evidence bucket remains private.

## 5. Build React and publish the frontend

- [ ] 5.1 Complete the React/Vite/TypeScript UI for upload-and-create, list, detail/download, delete confirmation, loading, empty, success, validation, not-found, and dependency-failure states.
- [ ] 5.2 Configure `VITE_API_BASE_URL` with the REST API invoke base ending in `/prod`, without a trailing slash, and keep AWS credentials, bucket names, and generated URLs out of frontend source.
- [ ] 5.3 Write failing frontend tests first, implement the centralized typed API client and user flows, and pass tests and type checks.
- [ ] 5.4 Run the Vite production build.
- [ ] 5.5 In the S3 Console, create the separate frontend bucket, configure static website hosting, and grant public read only to built website objects.
- [ ] 5.6 Upload the production build output through the S3 Console and record the exact website origin.
- [ ] 5.7 Replace localhost with that exact website origin in `/uploads/presign`, `/evidence`, and `/evidence/{id}` REST `OPTIONS` responses and Gateway Responses `DEFAULT_4XX` and `DEFAULT_5XX`. Update all five Lambdas' `ALLOWED_ORIGIN` to the same origin.
- [ ] 5.8 Add the website origin alongside `http://localhost:5173` in private evidence-bucket CORS; preserve `GET`, `HEAD`, and `PUT` and keep Block Public Access enabled.
- [ ] 5.9 Explicitly redeploy the REST API to `prod`, then complete an end-to-end check of all five final API routes from the deployed frontend and confirm `/workshop` does not exist.
