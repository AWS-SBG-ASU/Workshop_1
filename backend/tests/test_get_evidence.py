import json
from pathlib import Path

from functions.get_evidence import lambda_function

EVENT_PATH = Path(__file__).parents[1] / "events" / "get_evidence_demo_id.json"


def load_event():
    return json.loads(EVENT_PATH.read_text(encoding="utf-8"))


def test_parses_get_path_and_id_path_parameter():
    request = lambda_function.ApiRequest.from_event(load_event())

    assert request.method == "GET"
    assert request.path == "/evidence/demo-id"
    assert request.resource == "/evidence/{id}"
    assert request.stage == "prod"
    assert request.body is None
    assert request.path_parameters == {"id": "demo-id"}
    assert request.query_parameters == {}


def test_rejects_missing_or_malformed_resource_context_and_stage():
    invalid_events = []

    event = load_event()
    event.pop("resource")
    invalid_events.append(event)

    event = load_event()
    event["resource"] = "evidence/{id}"
    invalid_events.append(event)

    event = load_event()
    event.pop("requestContext")
    invalid_events.append(event)

    event = load_event()
    event["requestContext"] = []
    invalid_events.append(event)

    event = load_event()
    event["requestContext"] = {}
    invalid_events.append(event)

    event = load_event()
    event["requestContext"]["stage"] = ""
    invalid_events.append(event)

    for invalid_event in invalid_events:
        response = lambda_function.lambda_handler(invalid_event, None)

        assert response["statusCode"] == 400
        assert json.loads(response["body"])["error"]["code"] == "INVALID_REQUEST"


def test_rejects_stage_other_than_prod():
    event = load_event()
    event["requestContext"]["stage"] = "dev"

    response = lambda_function.lambda_handler(event, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"]["code"] == "INVALID_REQUEST"


def test_rejects_mismatched_resource_template():
    event = load_event()
    event["resource"] = "/evidence"

    response = lambda_function.lambda_handler(event, None)

    assert response["statusCode"] == 404
    assert json.loads(response["body"])["error"]["code"] == "NOT_FOUND"


def test_builds_api_gateway_response_model(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://app.example.com")
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "https://app.example.com",
        "Access-Control-Allow-Headers": "Content-Type,Accept",
        "Access-Control-Allow-Methods": "GET,DELETE,OPTIONS",
    }

    response = lambda_function.ApiResponse(
        200, {"id": "demo-id"}, "GET,DELETE,OPTIONS"
    ).to_dict()
    bodyless_response = lambda_function.ApiResponse(
        204, None, "GET,DELETE,OPTIONS"
    ).to_dict()

    assert response == {
        "statusCode": 200,
        "headers": headers,
        "body": '{"id":"demo-id"}',
    }
    assert bodyless_response == {"statusCode": 204, "headers": headers}


def test_declares_canonical_contract():
    source = Path(lambda_function.__file__).read_text(encoding="utf-8")

    assert lambda_function.PATH_PARAMETER == "id"
    assert lambda_function.REQUIRED_ENVIRONMENT == ("ALLOWED_ORIGIN", "TABLE_NAME")
    assert "phase 3" in source
    assert "GetItem" in source
    assert "404" in source
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


def test_rejects_path_parameter_mismatch():
    event = load_event()
    event["pathParameters"]["id"] = "other-id"

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
