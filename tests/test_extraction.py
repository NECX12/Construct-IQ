import pytest

from app.extraction import AIProviderError, _generate_with_fallback, _generate_with_retry
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


def test_gemini_503_uses_fallback_model_after_primary_retries():
    requested_models = []

    def operation_for_model(model):
        requested_models.append(model)

        def operation():
            if model == "primary-model":
                raise RuntimeError("503 UNAVAILABLE")
            return "fallback result"

        return operation

    result, used_fallback = _generate_with_fallback(
        "primary-model",
        "fallback-model",
        operation_for_model,
        sleep=lambda _delay: None,
    )

    assert result == "fallback result"
    assert used_fallback is True
    assert requested_models == ["primary-model", "fallback-model"]


def test_gemini_quota_error_does_not_switch_models():
    requested_models = []

    def operation_for_model(model):
        requested_models.append(model)
        return lambda: (_ for _ in ()).throw(RuntimeError("429 RESOURCE_EXHAUSTED"))

    with pytest.raises(AIProviderError, match="rate-limited"):
        _generate_with_fallback(
            "primary-model",
            "fallback-model",
            operation_for_model,
            sleep=lambda _delay: None,
        )

    assert requested_models == ["primary-model"]
