import json
from pathlib import Path

from functions.list_evidence import lambda_function

EVENT_PATH = Path(__file__).parents[1] / "events" / "get_evidence.json"


def load_event():
    return json.loads(EVENT_PATH.read_text(encoding="utf-8"))


def test_parses_get_path_without_query_parameters():
    request = lambda_function.ApiRequest.from_event(load_event())

    assert request.method == "GET"
    assert request.path == "/evidence"
    assert request.body is None
    assert request.path_parameters == {}
    assert request.query_parameters == {}


def test_builds_api_gateway_response_model(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://app.example.com")
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "https://app.example.com",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,GET",
    }

    response = lambda_function.ApiResponse(
        200, {"items": []}, "OPTIONS,GET"
    ).to_dict()
    bodyless_response = lambda_function.ApiResponse(
        204, None, "OPTIONS,GET"
    ).to_dict()

    assert response == {
        "statusCode": 200,
        "headers": headers,
        "body": '{"items":[]}',
    }
    assert bodyless_response == {"statusCode": 204, "headers": headers}


def test_declares_canonical_contract():
    source = Path(lambda_function.__file__).read_text(encoding="utf-8")

    assert lambda_function.REQUIRED_ENVIRONMENT == ("ALLOWED_ORIGIN", "TABLE_NAME")
    assert "phase 3" in source
    assert "USER#demo" in source
    assert "newest first" in source
    assert "no Scan" in source
    assert "phase 4" in source
    assert "ASSET_BUCKET" in source
    assert "DOWNLOAD_URL_EXPIRY_SECONDS" in source
    assert "assetUrl" in source
    assert "s3:GetObject" in source


def test_returns_controlled_not_implemented_response(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://app.example.com")
    monkeypatch.setenv("TABLE_NAME", "test-value")

    response = lambda_function.lambda_handler(load_event(), None)

    assert response["statusCode"] == 501
    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["Access-Control-Allow-Origin"] == "https://app.example.com"
    assert json.loads(response["body"])["error"]["code"] == "NOT_IMPLEMENTED"


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


def test_rejects_wrong_method_for_route():
    event = load_event()
    event["requestContext"]["http"]["method"] = "POST"

    response = lambda_function.lambda_handler(event, None)

    assert response["statusCode"] == 405
    assert json.loads(response["body"])["error"]["code"] == "METHOD_NOT_ALLOWED"
