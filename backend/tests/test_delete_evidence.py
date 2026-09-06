import json
from pathlib import Path

from functions.delete_evidence import lambda_function

EVENT_PATH = Path(__file__).parents[1] / "events" / "delete_evidence_demo_id.json"


def load_event():
    return json.loads(EVENT_PATH.read_text(encoding="utf-8"))


def test_parses_delete_path_and_id_path_parameter():
    request = lambda_function.ApiRequest.from_event(load_event())

    assert request.method == "DELETE"
    assert request.path == "/evidence/demo-id"
    assert request.body is None
    assert request.path_parameters == {"id": "demo-id"}
    assert request.query_parameters == {}


def test_builds_api_gateway_response_model(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://app.example.com")
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "https://app.example.com",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,DELETE",
    }

    response = lambda_function.ApiResponse(
        404, {"error": {"code": "NOT_FOUND", "message": "Not found."}}, "OPTIONS,DELETE"
    ).to_dict()
    bodyless_response = lambda_function.ApiResponse(
        204, None, "OPTIONS,DELETE"
    ).to_dict()

    assert response == {
        "statusCode": 404,
        "headers": headers,
        "body": '{"error":{"code":"NOT_FOUND","message":"Not found."}}',
    }
    assert bodyless_response == {"statusCode": 204, "headers": headers}


def test_declares_canonical_contract():
    source = Path(lambda_function.__file__).read_text(encoding="utf-8")

    assert lambda_function.PATH_PARAMETER == "id"
    assert lambda_function.REQUIRED_ENVIRONMENT == ("ALLOWED_ORIGIN", "TABLE_NAME")
    assert "phase 3" in source
    assert "404" in source
    assert "phase 4" in source
    assert "ASSET_BUCKET" in source
    assert "exact S3 asset" in source
    assert "first" in source
    assert "then DeleteItem" in source
    assert "empty 204" in source


def test_returns_controlled_not_implemented_response(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://app.example.com")
    monkeypatch.setenv("TABLE_NAME", "test-value")

    response = lambda_function.lambda_handler(load_event(), None)

    assert response["statusCode"] == 501
    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["Access-Control-Allow-Origin"] == "https://app.example.com"
    assert json.loads(response["body"])["error"]["code"] == "NOT_IMPLEMENTED"


def test_rejects_missing_path_parameter():
    event = load_event()
    event.pop("pathParameters")

    response = lambda_function.lambda_handler(event, None)

    assert response["statusCode"] == 404
    assert json.loads(response["body"])["error"]["code"] == "NOT_FOUND"


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
