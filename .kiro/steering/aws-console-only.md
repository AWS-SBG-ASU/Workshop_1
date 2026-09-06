---
inclusion: always
---

# AWS Console-Only Provisioning

Provision, configure, inspect, and validate AWS resources only in the AWS Management Console.

## Required behavior

- Create API Gateway, Lambda, DynamoDB, IAM, and S3 resources through their console pages.
- Configure HTTP API integrations, routes, stages, CORS, Lambda triggers, environment variables, permissions, and S3 website settings in the console.
- Copy each standalone handler into the Lambda code editor as `lambda_function.py`.
- Use Lambda Console API Gateway HTTP API payload format 2.0 test events after every handler change.
- Record resource names, ARNs, invoke URLs, environment variables, IAM actions/resources, event payloads, and expected results as explicit handoff information.

## Prohibited provisioning paths

Do not execute AWS CLI, SAM, CDK, Terraform, OpenTofu, Pulumi, Serverless Framework, or `sls` commands. Do not add infrastructure templates, deployment scripts, or command-line provisioning instructions. Local commands are limited to code tests, type checks, linting, and frontend builds that do not create or modify AWS resources.

## Safety

Use least-privilege IAM policies, keep the evidence bucket private with Block Public Access enabled, and expose only the static frontend assets required for S3 website hosting. Never place credentials or presigned URLs in source, logs, or documentation.