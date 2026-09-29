import pytest

from app.extraction import AIProviderError, _generate_with_retry
from app.models import AIExtractionResponse


def test_gemini_response_schema_has_no_free_form_properties():
    schema = str(AIExtractionResponse.model_json_schema())
    assert "additionalProperties" not in schema


def test_gemini_transient_error_is_retried():
    attempts = 0
    delays = []

    def operation():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("503 UNAVAILABLE")
        return "success"

    result = _generate_with_retry(operation, sleep=delays.append)

    assert result == "success"
    assert attempts == 2
    assert delays == [1]


def test_gemini_transient_error_returns_actionable_message_after_retries():
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        raise RuntimeError("503 UNAVAILABLE")

    with pytest.raises(AIProviderError, match="after 3 attempts"):
        _generate_with_retry(operation, sleep=lambda _delay: None)

    assert attempts == 3


def test_gemini_permanent_error_is_not_retried():
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        raise RuntimeError("401 UNAUTHENTICATED")

    with pytest.raises(RuntimeError, match="UNAUTHENTICATED"):
        _generate_with_retry(operation, sleep=lambda _delay: None)

    assert attempts == 1
