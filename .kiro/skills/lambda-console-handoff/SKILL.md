---
name: lambda-console-handoff
description: Produce a complete, copy-ready AWS Lambda Console handoff after a ProofStack handler is created or changed.
---

# Lambda Console Handoff

Use this skill after creating or changing any ProofStack Lambda handler. Run the focused local test first, then produce a concise handoff that can be completed entirely in the AWS Management Console.

## Preconditions

- The handler is standalone Python with no project-local imports.
- The full file can be copied into `lambda_function.py`.
- The entry point is `lambda_handler`.
- The event is an API Gateway REST API Lambda proxy event for named stage `prod`.
- Local tests use mocked or fake AWS clients and do not contact AWS.

## Required output

Return every section below. Do not omit empty sections; write `None` with a short reason when a value is not required.

### 1. Handler

- Local source path
- Lambda function name
- Runtime and architecture
- Console file: `lambda_function.py`
- Handler setting: `lambda_function.lambda_handler`
- Confirmation that the file is standalone and copy-ready

### 2. Environment variables

Provide a table with:

| Name | Value source | Required | Purpose |
| ---- | ------------ | -------: | ------- |

Use placeholders for console-created values. Never include credentials or secrets.

### 3. IAM actions and resources

Provide a least-privilege table with:

| Effect | Action | Resource ARN pattern | Reason |
| ------ | ------ | -------------------- | ------ |

List exact applicable DynamoDB and S3 needs. Do not use `*` resources when a table, bucket, or object prefix can be scoped.

### 4. Lambda Console event

Provide one complete JSON event for the changed behavior. It must include:

- top-level `httpMethod`, actual `path`, and templated `resource`
- headers including `content-type` when a body is present
- `pathParameters.id` for `/evidence/{id}` requests, or `pathParameters: null` otherwise
- `requestContext.stage` set to `prod`
- a JSON-string `body` when applicable, or `body: null`
- `isBase64Encoded: false`

Use non-sensitive sample values. A representative event shape is:

```json
{
  "httpMethod": "GET",
  "path": "/evidence/demo-id",
  "resource": "/evidence/{id}",
  "headers": { "accept": "application/json" },
  "pathParameters": { "id": "demo-id" },
  "requestContext": { "stage": "prod" },
  "body": null,
  "isBase64Encoded": false
}
```

### 5. Expected result

State the expected status code, required headers, and parsed response body. For successful delete, state `204` and no body. Also identify the expected DynamoDB or S3 side effect.

### 6. Local test command and result

Provide:

- Exact focused local test command
- Exit status
- Passed/failed test count
- Concise result summary

Do not claim a result unless the command was run. If it could not run, state the blocker and the next-best validation.

### 7. AWS Console setup steps

Give ordered console steps covering only what applies:

1. Open or create the Lambda function with the required Python runtime.
2. Paste the standalone source into `lambda_function.py` and deploy it.
3. Set the handler value and environment variables.
4. Attach or update the least-privilege execution-role permissions.
5. In the Regional REST API, open the exact resource and business method, choose the Lambda, and enable Lambda proxy integration.
6. Confirm the business method and its resource's `OPTIONS` method both use **Authorization** `NONE` and **API Key Required** false. Confirm API Gateway can invoke the function, `OPTIONS` uses a MOCK integration, and `DEFAULT_4XX` and `DEFAULT_5XX` CORS exists.
7. Explicitly deploy or redeploy the API to stage `prod` if the method, integration, permissions, CORS, or Gateway Responses changed. Record the invoke base ending in `/prod`.
8. Create the named Lambda Console test event from the supplied JSON.
9. Run the event and compare status, headers, body, logs, and side effects with the expected result.

## Verification rule

A handler handoff is incomplete until its focused local test result and Lambda Console REST proxy event for `prod` are both included. It must also state whether `prod` redeployment is required. Never provide AWS CLI, SAM, CDK, Terraform, OpenTofu, Pulumi, Serverless Framework, or `sls` instructions.
