# Console-only cleanup

Perform cleanup in `us-east-1` after confirming the recorded resource names and account. These actions permanently remove the application endpoint, stored metadata, and files. Before teardown, use ProofStack's delete operation for any evidence that must follow the normal record-and-file lifecycle; do not manage application data through DynamoDB or S3 data pages.

## Safe deletion order

1. **Stop browser traffic.** Open the public website bucket → **Properties** → **Static website hosting** → **Edit** → **Disable**.
2. **Delete the HTTP API.** Open **API Gateway** → **APIs**, select `ProofStackApi`, and choose **Delete**. This removes routes, integrations, the `$default` stage, CORS settings, and the public invoke endpoint before compute or data resources are removed.
3. **Delete the five Lambda functions.** In **Lambda** → **Functions**, delete `proofstack-presign-upload`, `proofstack-create-evidence`, `proofstack-list-evidence`, `proofstack-get-evidence`, and `proofstack-delete-evidence`.
4. **Delete Lambda execution roles.** In **IAM** → **Roles**, open each role created for those functions, verify it is no longer attached to a function, remove its inline resource policies if required, and delete it. Do not delete shared roles.
5. **Delete the private evidence bucket.** In **S3** → **Buckets**, select the recorded asset bucket, choose **Empty**, type the confirmation, then choose **Delete**. Verify Block Public Access remained enabled until deletion. If versioning was enabled, permanently remove all object versions and delete markers during the empty operation.
6. **Delete the DynamoDB table.** Open **DynamoDB** → **Tables**, select `ProofStackEvidence`, choose **Delete**, acknowledge that all table data will be removed, and confirm. Disable deletion protection first only if it was enabled.
7. **Delete the public website bucket.** In **S3**, empty the recorded website bucket, including versions and delete markers if present, then delete the bucket. This also removes the uploaded build and public-read bucket policy.
8. **Remove log groups.** Open **CloudWatch** → **Logs** → **Log groups** and delete `/aws/lambda/proofstack-presign-upload`, `/aws/lambda/proofstack-create-evidence`, `/aws/lambda/proofstack-list-evidence`, `/aws/lambda/proofstack-get-evidence`, and `/aws/lambda/proofstack-delete-evidence`. Delete API Gateway log groups only if you created dedicated ones for `ProofStackApi`.
9. **Verify cleanup.** Confirm the API no longer appears in API Gateway, the five functions and their dedicated roles are absent, both bucket names are absent, and `ProofStackEvidence` is absent. Review the AWS Billing console for any remaining resources associated with the recorded names.

Keep local source and documentation. Remove uncommitted `frontend/.env.local`, `frontend/.env.production`, and generated `frontend/dist/` if they are no longer needed; they are already ignored by Git.
