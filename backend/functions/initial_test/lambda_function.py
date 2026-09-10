import json
import os


def lambda_handler(event, context):
    if (
        not isinstance(event, dict)
        or event.get("httpMethod") != "GET"
        or event.get("path") != "/workshop"
        or event.get("resource") != "/workshop"
        or (event.get("requestContext") or {}).get("stage") != "prod"
    ):
        return {
            "statusCode": 404,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": os.environ.get("ALLOWED_ORIGIN", "null"),
                "Access-Control-Allow-Headers": "content-type,accept",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": json.dumps(
                {"error": {"code": "NOT_FOUND", "message": "Route not found."}},
                separators=(",", ":"),
            ),
        }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": os.environ.get("ALLOWED_ORIGIN", "null"),
            "Access-Control-Allow-Headers": "content-type,accept",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps({"message": "Lambda is connected"}, separators=(",", ":")),
    }