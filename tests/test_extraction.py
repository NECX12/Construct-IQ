from app.models import AIExtractionResponse


def test_gemini_response_schema_has_no_free_form_properties():
    schema = str(AIExtractionResponse.model_json_schema())
    assert "additionalProperties" not in schema
