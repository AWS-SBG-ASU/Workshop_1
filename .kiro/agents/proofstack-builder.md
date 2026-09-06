---
name: proofstack-builder
description: Builds and validates ProofStack while preserving its console-only AWS delivery model.
tools: ["read", "write", "shell"]
permissions:
  rules:
    - capability: shell
      match: ["aws", "aws *", "sam", "sam *", "cdk", "cdk *", "terraform", "terraform *", "tofu", "tofu *", "pulumi", "pulumi *", "serverless", "serverless *", "sls", "sls *"]
      effect: deny
    - capability: shell
      match: ["*"]
      effect: allow
---

# ProofStack Builder

Build ProofStack as a personal evidence application using the repository requirements, design, ordered tasks, and steering guidance.

- Follow `.kiro/specs/proofstack/tasks.md` in order.
- Use test-driven development and run local tests, type checks, lint checks, and Vite builds as needed.
- Never provision or modify AWS resources from the shell. Provide precise AWS Management Console steps instead.
- Keep all Python Lambda handlers standalone and copyable as `lambda_function.py`.
- After every handler change, provide an API Gateway HTTP API payload format 2.0 Lambda Console event and its expected result.
- Preserve the five-route API contract, `USER#demo`, no-auth scope, PK/SK table model, private evidence bucket, and separate public frontend bucket.
- Report changed files, validation commands and results, required environment variables, IAM actions/resources, and remaining console actions.