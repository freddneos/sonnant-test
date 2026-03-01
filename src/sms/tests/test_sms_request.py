from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from src.core.config import settings
from src.main import app

# Instantiate test client
client = TestClient(app)


#####################################################################################################################
# Fixtures
#####################################################################################################################
@pytest.fixture
def valid_sms_request_data():
    return {"From": "+1234567890", "Body": "Hello!"}


@pytest.fixture
def invalid_sms_request_data():
    return {"From": "+1234567890", "Body": ""}  # Body is invalid (too short)


@pytest.fixture
def empty_sms_request_data():
    return {}  # Missing both From and Body


#####################################################################################################################
# Tests
#####################################################################################################################
def test_reply_valid_request(valid_sms_request_data):
    """
    Test the endpoint with a valid SMS request.
    """

    # Patch the agent.run method
    with patch(
        "src.sms.api.Agent.run",
        new=AsyncMock(return_value=type("MockResponse", (object,), {"data": "Hello, you said: Hello!"})),
    ), patch.object(settings, "TWILIO_WEBHOOKS_VALIDATION_ENABLED", False):
        response = client.post("/sms/reply", data=valid_sms_request_data)

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "text/xml; charset=utf-8"

        # Assert the TwiML response structure
        expected_response = (
            '<?xml version="1.0" encoding="UTF-8"?><Response><Message>Hello, you said: Hello!</Message></Response>'
        )
        assert response.text.strip() == expected_response


def test_reply_agent_run_connection_error(valid_sms_request_data):
    """
    Test the endpoint when Agent.run raises a httpx.ConnectTimeout exception.
    """

    # Patch the agent.run method to raise a ConnectTimeout exception
    with patch(
        "src.sms.api.Agent.run",
        new=AsyncMock(
            side_effect=httpx.ConnectTimeout(
                "Connection timed out", request=httpx.Request("POST", "https://api.example.com/test")
            )
        ),
    ), patch.object(settings, "TWILIO_WEBHOOKS_VALIDATION_ENABLED", False):
        # Send request to the endpoint
        response = client.post("/sms/reply", data=valid_sms_request_data)

        # Validate response
        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "text/xml; charset=utf-8"

        # Assert the TwiML response structure for timeout
        expected_response = (
            '<?xml version="1.0" encoding="UTF-8"?><Response>'
            "<Message>Ups! We were unable to respond to your request, please try again later :(</Message>"
            "</Response>"
        )
        assert response.text.strip() == expected_response


def test_reply_invalid_request_body(invalid_sms_request_data):
    """
    Test the endpoint with an invalid SMS request (Body too short).
    """

    with patch.object(settings, "TWILIO_WEBHOOKS_VALIDATION_ENABLED", False):
        response = client.post("/sms/reply", data=invalid_sms_request_data)

        assert response.status_code == HTTPStatus.OK
        assert "Ups!" in response.text


def test_reply_missing_data(empty_sms_request_data):
    """
    Test the endpoint with missing data in the SMS request.
    """

    response = client.post("/sms/reply", data=empty_sms_request_data)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    response_json = response.json()
    assert len(response_json["detail"]) == 2
    assert "Field required" in response.json()["detail"][0]["msg"]
    assert "Field required" in response.json()["detail"][1]["msg"]


def test_reply_missing_from_field(valid_sms_request_data):
    """
    Test the endpoint with missing 'From' field.
    """

    data = valid_sms_request_data.copy()
    del data["From"]

    response = client.post("/sms/reply", data=data)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "Field required" in response.json()["detail"][0]["msg"]


def test_reply_missing_body_field(valid_sms_request_data):
    """
    Test the endpoint with missing 'Body' field.
    """

    data = valid_sms_request_data.copy()
    del data["Body"]

    response = client.post("/sms/reply", data=data)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "Field required" in response.json()["detail"][0]["msg"]


def test_reply_with_valid_twilio_signature(valid_sms_request_data):
    """
    Test the reply endpoint with a valid Twilio signature.
    """

    # Mock Twilio signature validation
    with patch("twilio.request_validator.RequestValidator.validate", return_value=True), patch(
        "src.sms.api.Agent.run",
        new=AsyncMock(return_value=type("MockResponse", (object,), {"data": "Hello, you said: Hello!"})),
    ), patch.object(settings, "TWILIO_AUTH_TOKEN", "12345"):
        response = client.post(
            "/sms/reply", data=valid_sms_request_data, headers={"X-Twilio-Signature": "valid_signature"}
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "text/xml; charset=utf-8"

        # Expected TwiML response
        expected_response = (
            '<?xml version="1.0" encoding="UTF-8"?><Response><Message>Hello, you said: Hello!</Message></Response>'
        )
        assert response.text.strip() == expected_response


def test_reply_with_invalid_signature_format(valid_sms_request_data):
    """
    Test the reply endpoint when Twilio signature is invalid (e.g., wrong format).
    """
    # Mock Twilio signature validation and Agent.run method
    with patch("twilio.request_validator.RequestValidator.validate", return_value=False), patch.object(
        settings, "TWILIO_WEBHOOKS_VALIDATION_ENABLED", True
    ), patch.object(settings, "TWILIO_AUTH_TOKEN", "12345"):
        signature = "invalid_signature_format"
        response = client.post("/sms/reply", data=valid_sms_request_data, headers={"X-Twilio-Signature": signature})

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert "Forbidden" in response.text
