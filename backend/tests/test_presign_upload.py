import base64
import json
from pathlib import Path

from functions.presign_upload import lambda_function

EVENT_PATH = Path(__file__).parents[1] / "events" / "post_uploads_presign.json"


def load_event():
    return json.loads(EVENT_PATH.read_text(encoding="utf-8"))


def test_parses_post_path_and_json_body():
    request = lambda_function.ApiRequest.from_event(load_event())

    assert request.method == "POST"
    assert request.path == "/uploads/presign"
    assert request.body == {"fileName": "receipt.pdf", "contentType": "application/pdf"}
    assert request.path_parameters == {}
    assert request.query_parameters == {}


def test_parses_base64_encoded_json_body():
    event = load_event()
    event["body"] = base64.b64encode(event["body"].encode("utf-8")).decode("ascii")
    event["isBase64Encoded"] = True

    request = lambda_function.ApiRequest.from_event(event)

    assert request.body["fileName"] == "receipt.pdf"


def test_builds_api_gateway_response_model(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://app.example.com")
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "https://app.example.com",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
    }

    response = lambda_function.ApiResponse(
        200, {"assetKey": "evidence/demo/demo-id/receipt.pdf"}, "OPTIONS,POST"
    ).to_dict()
    bodyless_response = lambda_function.ApiResponse(
        204, None, "OPTIONS,POST"
    ).to_dict()

    assert response == {
        "statusCode": 200,
        "headers": headers,
        "body": '{"assetKey":"evidence/demo/demo-id/receipt.pdf"}',
    }
    assert bodyless_response == {"statusCode": 204, "headers": headers}


def test_declares_canonical_contract():
    source = Path(lambda_function.__file__).read_text(encoding="utf-8")

    assert lambda_function.REQUIRED_ENVIRONMENT == (
        "ALLOWED_ORIGIN",
        "ASSET_BUCKET",
        "UPLOAD_URL_EXPIRY_SECONDS",
    )
    assert "evidence/demo/" in source
    assert "assetKey" in source
    assert "s3:PutObject" in source


def test_returns_controlled_not_implemented_response(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://app.example.com")
    monkeypatch.setenv("ASSET_BUCKET", "test-value")
    monkeypatch.setenv("UPLOAD_URL_EXPIRY_SECONDS", "300")

    response = lambda_function.lambda_handler(load_event(), None)

    assert response["statusCode"] == 501
    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["Access-Control-Allow-Origin"] == "https://app.example.com"
    assert json.loads(response["body"]) == {
        "error": {
            "code": "NOT_IMPLEMENTED",
            "message": "Upload URL creation is not implemented.",
        }
    }


def test_rejects_invalid_json_without_raising():
    event = load_event()
    event["body"] = "{"

    response = lambda_function.lambda_handler(event, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"]["code"] == "INVALID_REQUEST"


def test_reports_missing_configuration_without_aws_access(monkeypatch):
    for name in ("ALLOWED_ORIGIN", "ASSET_BUCKET", "UPLOAD_URL_EXPIRY_SECONDS"):
        monkeypatch.delenv(name, raising=False)

    def fail_aws_access(*args, **kwargs):
        raise AssertionError("AWS access was attempted")

    monkeypatch.setattr(lambda_function.boto3, "client", fail_aws_access)
    monkeypatch.setattr(lambda_function.boto3, "resource", fail_aws_access)

    response = lambda_function.lambda_handler(load_event(), None)

    assert response["statusCode"] == 500
    assert json.loads(response["body"])["error"]["code"] == "CONFIGURATION_ERROR"
