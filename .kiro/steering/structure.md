---
inclusion: always
---

# Repository Structure

Keep responsibilities within these paths:

```text
frontend/                         React/Vite/TypeScript application
backend/                          standalone Python Lambda handlers and local tests
.kiro/specs/proofstack/           product requirements, design, and ordered tasks
.kiro/steering/                   persistent repository conventions
.kiro/agents/                     custom agent configuration
.kiro/skills/                     reusable execution handoffs
```

## Placement rules

- Store one deployable Lambda handler per backend source file. Do not create shared project-local runtime modules that prevent direct Lambda Console copy/paste.
- Keep backend tests separate from deployable handler contents and name them for the handler behavior they verify.
- Keep frontend API types and request logic centralized rather than duplicating fetch calls across components.
- Keep UI components focused on presentation and move multi-step upload/create coordination into feature-level code.
- Do not commit build output, local environment files, credentials, presigned URLs, bucket names, table names, or generated test artifacts.
- Update requirements, design, or tasks when the product contract changes; do not let guidance and implementation diverge.