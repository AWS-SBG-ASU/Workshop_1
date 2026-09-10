---
inclusion: fileMatch
fileMatchPattern: ["frontend/**/*.ts", "frontend/**/*.tsx", "frontend/**/*.css", "frontend/**/*.html"]
---

# Frontend Conventions

- Use React functional components and strict TypeScript types; avoid `any`.
- Read the deployed Regional REST API invoke base from `import.meta.env.VITE_API_BASE_URL`. It includes the named stage suffix `/prod` and has no trailing slash; normalize URL joining in one typed API client.
- Keep all five route contracts centralized. Item routes use `id`; presign accepts `fileName` and `contentType` and returns `uploadUrl`, `assetKey`, and `expiresIn`.
- Use `assetKey`. Treat phase-4 `assetUrl` values as temporary response data and never persist or log them.
- Parse errors only from `{"error":{"code":"...","message":"..."}}` and handle an empty successful `204` delete.
- Implement file upload as presign request -> direct S3 PUT -> metadata create. Do not create metadata when upload fails.
- Expect the complete newest-first list in one response; do not implement pagination.
- Provide visible loading, progress or status, empty, success, validation, not-found, dependency-failure, and delete-confirmation states.
- Generate accessible forms with associated labels, keyboard-operable controls, useful focus behavior, and status announcements.
- Never include AWS credentials, IAM data, table names, private bucket names, or hard-coded deployment URLs in browser source.
- Write focused tests before behavior changes and keep network calls mocked at the API-client boundary.
- Require a passing TypeScript check, frontend test suite, and Vite production build before deployment. After the website origin is recorded, replace localhost in REST `OPTIONS`, Gateway Responses, and Lambda `ALLOWED_ORIGIN`, then redeploy `prod` before end-to-end testing.
