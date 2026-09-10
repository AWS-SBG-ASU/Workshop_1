import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from functions.create_evidence import lambda_function

EVENT_PATH = Path(__file__).parents[1] / "events" / "post_evidence.json"


def load_event():
    return json.loads(EVENT_PATH.read_text(encoding="utf-8"))


def parsed_body(response):
    body = json.loads(response["body"])
    if response["statusCode"] >= 400:
        assert set(body) == {"error"}
        assert set(body["error"]) == {"code", "message"}
    return body


def configured(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://app.example.com")
    monkeypatch.setenv("TABLE_NAME", "proofstack-test")


def test_parses_post_path_and_json_body():
    request = lambda_function.ApiRequest.from_event(load_event())

    assert request.method == "POST"
    assert request.path == "/evidence"
    assert request.resource == "/evidence"
    assert request.stage == "prod"
    assert request.body == {
        "title": "Cloud architecture certificate",
        "description": "Certificate confirming completion of a cloud architecture assessment.",
        "tags": ["certification", "cloud"],
        "fileName": "cloud-architecture-certificate.pdf",
        "contentType": "application/pdf",
        "assetKey": "evidence/demo/demo-id/cloud-architecture-certificate.pdf",
    }
    assert request.path_parameters == {}
    assert request.query_parameters == {}


def test_rejects_missing_or_malformed_resource_context_and_stage():
    invalid_events = []

    event = load_event()
    event.pop("resource")
    invalid_events.append(event)

    event = load_event()
    event["resource"] = "evidence"
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
        assert parsed_body(response)["error"]["code"] == "INVALID_REQUEST"


def test_rejects_stage_other_than_prod():
    event = load_event()
    event["requestContext"]["stage"] = "dev"

    response = lambda_function.lambda_handler(event, None)

    assert response["statusCode"] == 400
    assert parsed_body(response)["error"]["code"] == "INVALID_REQUEST"


def test_rejects_mismatched_resource_template():
    event = load_event()
    event["resource"] = "/uploads/presign"

    response = lambda_function.lambda_handler(event, None)

    assert response["statusCode"] == 404
    assert parsed_body(response)["error"]["code"] == "NOT_FOUND"


def test_builds_api_gateway_response_model(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://app.example.com")
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "https://app.example.com",
        "Access-Control-Allow-Headers": "Content-Type,Accept",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    }

    response = lambda_function.ApiResponse(
        201, {"id": "demo-id"}, "GET,POST,OPTIONS"
    ).to_dict()
    bodyless_response = lambda_function.ApiResponse(
        204, None, "GET,POST,OPTIONS"
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


def test_creates_evidence_with_server_owned_keys(monkeypatch):
    configured(monkeypatch)
    stored = []

    class FakeTable:
        def put_item(self, **kwargs):
            stored.append(kwargs)

    monkeypatch.setattr(lambda_function, "get_table", lambda table_name: FakeTable())
    monkeypatch.setattr(
        lambda_function,
        "current_utc_time",
        lambda: datetime(2025, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(lambda_function, "new_uuid_segment", lambda: "a1b2c3d4")

    event = load_event()
    request_body = json.loads(event["body"])
    request_body.update(
        {
            "title": "  Cloud architecture certificate  ",
            "description": "  Certificate confirming completion of a cloud architecture assessment.  ",
            "tags": [" certification ", "cloud"],
            "fileName": "  cloud-architecture-certificate.pdf  ",
            "contentType": "  application/pdf  ",
            "PK": "ATTACKER",
            "SK": "ATTACKER",
            "id": "caller-controlled",
        }
    )
    event["body"] = json.dumps(request_body)

    response = lambda_function.lambda_handler(event, None)

    assert response["statusCode"] == 201
    assert response["headers"]["Access-Control-Allow-Origin"] == "https://app.example.com"
    assert response["headers"]["Content-Type"] == "application/json"
    record = parsed_body(response)
    assert record == {
        "id": "20250102T030405123456Z-a1b2c3d4",
        "title": "Cloud architecture certificate",
        "description": "Certificate confirming completion of a cloud architecture assessment.",
        "tags": ["certification", "cloud"],
        "fileName": "cloud-architecture-certificate.pdf",
        "contentType": "application/pdf",
        "assetKey": "evidence/demo/demo-id/cloud-architecture-certificate.pdf",
        "createdAt": "2025-01-02T03:04:05.123456Z",
    }
    assert stored == [
        {
            "Item": {
                "PK": "USER#demo",
                "SK": "EVIDENCE#20250102T030405123456Z-a1b2c3d4",
                **record,
            }
        }
    ]
    assert "PK" not in record
    assert "SK" not in record


@pytest.mark.parametrize(
    ("body", "message_fragment"),
    [
        (None, "JSON object"),
        ([], "JSON object"),
        ({}, "title"),
        ({"title": "   "}, "title"),
        (
            {
                "title": "Professional record",
                "tags": "certification",
                "fileName": "professional-record.pdf",
                "contentType": "application/pdf",
                "assetKey": "evidence/demo/file.pdf",
            },
            "tags",
        ),
        (
            {
                "title": "Professional record",
                "tags": ["valid", "   "],
                "fileName": "professional-record.pdf",
                "contentType": "application/pdf",
                "assetKey": "evidence/demo/file.pdf",
            },
            "tags",
        ),
        (
            {
                "title": "Professional record",
                "tags": [],
                "fileName": "",
                "contentType": "application/pdf",
                "assetKey": "evidence/demo/file.pdf",
            },
            "fileName",
        ),
        (
            {
                "title": "Professional record",
                "tags": [],
                "fileName": "professional-record.pdf",
                "contentType": "not-a-mime-type",
                "assetKey": "evidence/demo/file.pdf",
            },
            "contentType",
        ),
        (
            {
                "title": "Professional record",
                "tags": [],
                "fileName": "professional-record.pdf",
                "contentType": "application/pdf",
                "assetKey": "another-user/file.pdf",
            },
            "assetKey",
        ),
    ],
)
def test_rejects_invalid_metadata_before_aws_access(monkeypatch, body, message_fragment):
    configured(monkeypatch)

    def fail_aws_access(*args, **kwargs):
        raise AssertionError("AWS access was attempted")

    monkeypatch.setattr(lambda_function.boto3, "resource", fail_aws_access)
    event = load_event()
    event["body"] = json.dumps(body)

    response = lambda_function.lambda_handler(event, None)

    assert response["statusCode"] == 400
    error = parsed_body(response)["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert message_fragment in error["message"]


def test_rejects_malformed_json_without_raising(monkeypatch):
    configured(monkeypatch)
    event = load_event()
    event["body"] = "{not-json"

    response = lambda_function.lambda_handler(event, None)

    assert response["statusCode"] == 400
    assert parsed_body(response)["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.parametrize(
    "event",
    [
        None,
        {},
        {"httpMethod": "POST"},
        {"path": "/evidence"},
        {"httpMethod": "POST", "path": "evidence"},
    ],
)
def test_rejects_malformed_rest_proxy_event_without_raising(event):
    response = lambda_function.lambda_handler(event, None)

    assert response["statusCode"] == 400
    assert parsed_body(response)["error"]["code"] == "INVALID_REQUEST"


def test_reports_missing_configuration_without_aws_access(monkeypatch):
    monkeypatch.delenv("ALLOWED_ORIGIN", raising=False)
    monkeypatch.delenv("TABLE_NAME", raising=False)

    def fail_aws_access(*args, **kwargs):
        raise AssertionError("AWS access was attempted")

    monkeypatch.setattr(lambda_function.boto3, "client", fail_aws_access)
    monkeypatch.setattr(lambda_function.boto3, "resource", fail_aws_access)

    response = lambda_function.lambda_handler(load_event(), None)

    assert response["statusCode"] == 500
    assert parsed_body(response)["error"]["code"] == "CONFIGURATION_ERROR"


def test_sanitizes_dynamodb_failure(monkeypatch):
    configured(monkeypatch)

    class FailingTable:
        def put_item(self, **kwargs):
            raise RuntimeError("secret dependency detail")

    monkeypatch.setattr(lambda_function, "get_table", lambda table_name: FailingTable())

    response = lambda_function.lambda_handler(load_event(), None)

    assert response["statusCode"] == 500
    error = parsed_body(response)["error"]
    assert error == {
        "code": "DEPENDENCY_ERROR",
        "message": "Evidence could not be saved.",
    }
    assert "secret dependency detail" not in response["body"]
