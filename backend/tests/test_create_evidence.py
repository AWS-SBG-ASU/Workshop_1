import json
from pathlib import Path

from functions.create_evidence import lambda_function

EVENT_PATH = Path(__file__).parents[1] / "events" / "post_evidence.json"


def load_event():
    return json.loads(EVENT_PATH.read_text(encoding="utf-8"))


def test_parses_post_path_and_json_body():
    request = lambda_function.ApiRequest.from_event(load_event())

    assert request.method == "POST"
    assert request.path == "/evidence"
    assert request.body == {
        "title": "Purchase receipt",
        "description": "Receipt for office supplies.",
        "tags": ["receipt", "office"],
        "assetKey": "evidence/demo/demo-id/receipt.pdf",
    }
    assert request.path_parameters == {}
    assert request.query_parameters == {}


def test_builds_api_gateway_response_model(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://app.example.com")
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "https://app.example.com",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
    }

    response = lambda_function.ApiResponse(
        201, {"id": "demo-id"}, "OPTIONS,POST"
    ).to_dict()
    bodyless_response = lambda_function.ApiResponse(
        204, None, "OPTIONS,POST"
    ).to_dict()

    assert response == {
        "statusCode": 201,
        "headers": headers,
        "body": '{"id":"demo-id"}',
    }
    assert bodyless_response == {"statusCode": 204, "headers": headers}


def test_declares_canonical_contract():
    source = Path(lambda_function.__file__).read_text(encoding="utf-8")

    assert lambda_function.REQUIRED_ENVIRONMENT == ("ALLOWED_ORIGIN", "TABLE_NAME")
    assert "Final action: DynamoDB PutItem" in source
    assert "evidence/demo/" in source
    assert "dynamodb:PutItem" in source
    assert "s3:" not in source


def test_returns_controlled_not_implemented_response(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://app.example.com")
    monkeypatch.setenv("TABLE_NAME", "test-value")

    response = lambda_function.lambda_handler(load_event(), None)

    assert response["statusCode"] == 501
    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["Access-Control-Allow-Origin"] == "https://app.example.com"
    assert json.loads(response["body"])["error"]["code"] == "NOT_IMPLEMENTED"


def test_rejects_non_v2_event_without_raising():
    event = load_event()
    event["version"] = "1.0"

    response = lambda_function.lambda_handler(event, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"]["code"] == "INVALID_REQUEST"


def test_reports_missing_configuration_without_aws_access(monkeypatch):
    monkeypatch.delenv("ALLOWED_ORIGIN", raising=False)
    monkeypatch.delenv("TABLE_NAME", raising=False)

    def fail_aws_access(*args, **kwargs):
        raise AssertionError("AWS access was attempted")

    monkeypatch.setattr(lambda_function.boto3, "client", fail_aws_access)
    monkeypatch.setattr(lambda_function.boto3, "resource", fail_aws_access)

    response = lambda_function.lambda_handler(load_event(), None)

    assert response["statusCode"] == 500
    assert json.loads(response["body"])["error"]["code"] == "CONFIGURATION_ERROR"
