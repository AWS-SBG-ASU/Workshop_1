"""API Gateway REST API handler for creating a private upload URL."""

import base64
import binascii
import json
import os

import boto3

EXPECTED_METHOD = "POST"
EXPECTED_PATH = "/uploads/presign"
EXPECTED_RESOURCE = "/uploads/presign"
EXPECTED_STAGE = "prod"
ALLOWED_METHODS = "POST,OPTIONS"
REQUIRED_ENVIRONMENT = ("ALLOWED_ORIGIN", "ASSET_BUCKET", "UPLOAD_URL_EXPIRY_SECONDS")


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
    if request.path != EXPECTED_PATH or request.resource != EXPECTED_RESOURCE:
        return ApiResponse(404, {"error": {"code": "NOT_FOUND", "message": "Route not found."}}, ALLOWED_METHODS).to_dict()
    if any(not os.environ.get(name) for name in REQUIRED_ENVIRONMENT):
        return ApiResponse(500, {"error": {"code": "CONFIGURATION_ERROR", "message": "Required service configuration is missing."}}, ALLOWED_METHODS).to_dict()

    # TODO (final): Create an assetKey under evidence/demo/, then generate a short-lived private PUT URL. Env: ALLOWED_ORIGIN, ASSET_BUCKET, UPLOAD_URL_EXPIRY_SECONDS. Workshop IAM: s3:PutObject with Resource: *.
    return ApiResponse(501, {"error": {"code": "NOT_IMPLEMENTED", "message": "Upload URL creation is not implemented."}}, ALLOWED_METHODS).to_dict()
