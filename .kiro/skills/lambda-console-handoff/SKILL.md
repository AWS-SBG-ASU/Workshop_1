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
- The event uses API Gateway HTTP API payload format 2.0.
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
|---|---|---:|---|

Use placeholders for console-created values. Never include credentials or secrets.

### 3. IAM actions and resources

Provide a least-privilege table with:

| Effect | Action | Resource ARN pattern | Reason |
|---|---|---|---|

List exact DynamoDB, S3, and logging needs. Do not use `*` resources when a table, bucket, object prefix, or log group can be scoped.

### 4. Lambda Console event

Provide one complete JSON event for the changed behavior. It must use payload format `2.0` and include the route key, raw path, HTTP method, headers, path parameters when applicable, and a JSON-string body when applicable. Use non-sensitive sample values.

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
5. Attach the API Gateway HTTP API trigger and exact method/route.
6. Confirm payload format 2.0 and CORS configuration.
7. Create the named test event from the supplied JSON.
8. Run the event and compare status, headers, body, logs, and side effects with the expected result.

## Verification rule

A handler handoff is incomplete until its focused local test result and Lambda Console API Gateway v2 test event are both included. Never provide AWS CLI, SAM, CDK, Terraform, OpenTofu, Pulumi, Serverless Framework, or `sls` instructions.