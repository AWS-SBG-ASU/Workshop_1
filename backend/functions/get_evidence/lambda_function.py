"""API Gateway REST API handler for retrieving an evidence record."""

import base64
import binascii
import json
import os

import boto3

EXPECTED_METHOD = "GET"
EXPECTED_RESOURCE = "/evidence/{id}"
EXPECTED_STAGE = "prod"
PATH_PARAMETER = "id"
ALLOWED_METHODS = "GET,DELETE,OPTIONS"
REQUIRED_ENVIRONMENT = ("ALLOWED_ORIGIN", "TABLE_NAME")


class InvalidRequest(ValueError):
    """Raised when a REST API Lambda proxy event cannot be parsed safely."""


class ApiRequest:
    """Normalized API Gateway REST API Lambda proxy request."""

    def __init__(self, method, path, resource, stage, body, path_parameters, query_parameters):
        self.method = method
        self.path = path
        self.resource = resource
        self.stage = stage
        self.body = body
        self.path_parameters = path_parameters
        self.query_parameters = query_parameters

    @classmethod
    def from_event(cls, event):
        """Create a normalized request from a REST API Lambda proxy event."""
        if not isinstance(event, dict):
            raise InvalidRequest("Expected an API Gateway REST API Lambda proxy event.")

        method = event.get("httpMethod")
        path = event.get("path")
        resource = event.get("resource")
        request_context = event.get("requestContext")
        if not isinstance(method, str) or not method.strip():
            raise InvalidRequest("The HTTP method is missing.")
        if not isinstance(path, str) or not path.startswith("/"):
            raise InvalidRequest("The request path is missing.")
        if not isinstance(resource, str) or not resource.startswith("/"):
            raise InvalidRequest("The request resource is missing.")
        if not isinstance(request_context, dict):
            raise InvalidRequest("The request context is missing.")
        stage = request_context.get("stage")
        if not isinstance(stage, str) or not stage.strip():
            raise InvalidRequest("The request stage is missing.")

        body = event.get("body")
        if event.get("isBase64Encoded", False) and body is not None:
            if not isinstance(body, str):
                raise InvalidRequest("The encoded request body must be text.")
            try:
                body = base64.b64decode(body, validate=True).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError) as exc:
                raise InvalidRequest("The encoded request body is invalid.") from exc

        parsed_body = None
        if body is not None and body != "":
            if not isinstance(body, str):
                raise InvalidRequest("The request body must be text.")
            try:
                parsed_body = json.loads(body)
            except json.JSONDecodeError as exc:
                raise InvalidRequest("The request body must contain valid JSON.") from exc

        path_parameters = event.get("pathParameters") or {}
        query_parameters = event.get("queryStringParameters") or {}
        if not isinstance(path_parameters, dict) or not isinstance(query_parameters, dict):
            raise InvalidRequest("Request parameters must be objects.")

        return cls(method.upper(), path, resource, stage, parsed_body, path_parameters, query_parameters)


class ApiResponse:
    """API Gateway REST API Lambda proxy JSON response."""

    def __init__(self, status_code, payload, allowed_methods):
        self.status_code = status_code
        self.payload = payload
        self.allowed_methods = allowed_methods

    def to_dict(self):
        response = {
            "statusCode": self.status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": os.environ.get("ALLOWED_ORIGIN", "null"),
                "Access-Control-Allow-Headers": "Content-Type,Accept",
                "Access-Control-Allow-Methods": self.allowed_methods,
            },
        }
        if self.payload is not None:
            response["body"] = json.dumps(self.payload, separators=(",", ":"))
        return response


def lambda_handler(event, context):
    """Validate the route and expose a stable starter response."""
    try:
        request = ApiRequest.from_event(event)
    except InvalidRequest as exc:
        return ApiResponse(400, {"error": {"code": "INVALID_REQUEST", "message": str(exc)}}, ALLOWED_METHODS).to_dict()

    if request.stage != EXPECTED_STAGE:
        return ApiResponse(400, {"error": {"code": "INVALID_REQUEST", "message": "The request stage is not supported."}}, ALLOWED_METHODS).to_dict()
    if request.method != EXPECTED_METHOD:
        return ApiResponse(405, {"error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed."}}, ALLOWED_METHODS).to_dict()
    evidence_id = request.path_parameters.get(PATH_PARAMETER)
    if (
        request.resource != EXPECTED_RESOURCE
        or not isinstance(evidence_id, str)
        or not evidence_id
        or request.path != "/evidence/" + evidence_id
    ):
        return ApiResponse(404, {"error": {"code": "NOT_FOUND", "message": "Route not found."}}, ALLOWED_METHODS).to_dict()
    if any(not os.environ.get(name) for name in REQUIRED_ENVIRONMENT):
        return ApiResponse(500, {"error": {"code": "CONFIGURATION_ERROR", "message": "Required service configuration is missing."}}, ALLOWED_METHODS).to_dict()

    # TODO (phase 3): GetItem for the USER#demo record and return 404 when it is absent. Env: ALLOWED_ORIGIN, TABLE_NAME. IAM: dynamodb:GetItem on arn:aws:dynamodb:${AWS_REGION}:${AWS_ACCOUNT_ID}:table/${TABLE_NAME}.
    # TODO (phase 4): Add ASSET_BUCKET and DOWNLOAD_URL_EXPIRY_SECONDS to issue an assetUrl for the record's assetKey. IAM: s3:GetObject on arn:aws:s3:::${ASSET_BUCKET}/evidence/demo/*.
    return ApiResponse(501, {"error": {"code": "NOT_IMPLEMENTED", "message": "Evidence retrieval is not implemented."}}, ALLOWED_METHODS).to_dict()
