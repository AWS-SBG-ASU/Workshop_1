---
inclusion: always
---

# AWS Console-Only Provisioning

Provision, configure, inspect, and validate AWS resources only in the AWS Management Console.

## Required behavior

- Create API Gateway, Lambda, DynamoDB, IAM, and S3 resources through their console pages.
- Create an API Gateway REST API with endpoint type **Regional**, resources `/uploads/presign`, `/evidence`, and `/evidence/{id}`, and named stage `prod`.
- Configure every business method with Lambda proxy integration. Configure every business method and every `OPTIONS` method with **Authorization** `NONE` and **API Key Required** false.
- Configure an `OPTIONS` method with a `MOCK` integration on each callable resource. Initially use origin `http://localhost:5173`, headers `content-type,accept`, and exact allowed-method lists `POST,OPTIONS`, `GET,POST,OPTIONS`, and `GET,DELETE,OPTIONS` for the three resources respectively.
- Configure CORS headers on Gateway Responses `DEFAULT_4XX` and `DEFAULT_5XX`.
- Explicitly use **Deploy API** to deploy the initial API and every later API change to `prod`; record the invoke base ending in `/prod`.
- Configure Lambda triggers, environment variables, permissions, private S3 CORS, and S3 website settings in the console.
- Copy each standalone handler into the Lambda code editor as `lambda_function.py`.
- Use Lambda Console API Gateway REST API Lambda proxy test events after every handler change. Events use top-level `httpMethod`, `path`, and `resource`, item `pathParameters.id`, and `requestContext.stage = "prod"`.
- During public frontend delivery in phase 5, replace localhost in the final REST `OPTIONS`, `DEFAULT_4XX`, `DEFAULT_5XX`, and all five Lambda `ALLOWED_ORIGIN` values with the website origin, then redeploy `prod`; private evidence-bucket CORS may retain both origins.
- Record resource names, ARNs, invoke URLs, environment variables, IAM actions/resources, event payloads, expected results, and deployment actions as explicit handoff information.

## Prohibited provisioning paths

Do not execute AWS CLI, SAM, CDK, Terraform, OpenTofu, Pulumi, Serverless Framework, or `sls` commands. Do not add infrastructure templates, deployment scripts, or command-line provisioning instructions. Local commands are limited to code tests, type checks, linting, and frontend builds that do not create or modify AWS resources.

## Safety

Use least-privilege IAM policies, keep the evidence bucket private with Block Public Access enabled, and expose only the static frontend assets required for S3 website hosting. Never place credentials or presigned URLs in source, logs, or documentation.
