import json
import mimetypes
import time
from pathlib import Path
from typing import Callable, TypeVar

from .config import settings
from .models import AIExtractionResponse, BuildingElement, DrawingExtraction
from .prompts import BLUEPRINT_EXTRACTION_PROMPT


class AIProviderError(RuntimeError):
    """Raised when the configured AI provider cannot complete extraction."""


ResponseT = TypeVar("ResponseT")


def _is_transient_gemini_error(error: Exception) -> bool:
    message = str(error).upper()
    return any(
        marker in message
        for marker in (
            "503",
            "UNAVAILABLE",
            "429",
            "RESOURCE_EXHAUSTED",
            "DEADLINE_EXCEEDED",
            "INTERNAL",
        )
    )


def _generate_with_retry(
    operation: Callable[[], ResponseT],
    sleep: Callable[[float], None] = time.sleep,
) -> ResponseT:
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            return operation()
        except Exception as exc:
            if not _is_transient_gemini_error(exc):
                raise
            if attempt == max_attempts - 1:
                raise AIProviderError(
                    "Gemini is temporarily busy or unavailable after 3 attempts. "
                    "Wait briefly and try uploading the drawing again."
                ) from exc
            sleep(2**attempt)
    raise AIProviderError("Gemini extraction did not complete")


def _mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    supported = {"application/pdf", "image/png", "image/jpeg", "image/webp"}
    if mime_type not in supported:
        raise ValueError("Gemini blueprint extraction supports PDF, PNG, JPG, and WEBP files")
    return mime_type


def _extract_with_gemini(filename: str, content: bytes) -> DrawingExtraction:
    if not settings.gemini_api_key:
        raise AIProviderError("GEMINI_API_KEY is missing. Add it to your local .env file.")

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise AIProviderError("The Gemini SDK is not installed. Run: python -m pip install -r requirements.txt") from exc

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = _generate_with_retry(
            lambda: client.models.generate_content(
                model=settings.model_name,
                contents=[
                    types.Part.from_bytes(data=content, mime_type=_mime_type(filename)),
                    BLUEPRINT_EXTRACTION_PROMPT,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AIExtractionResponse,
                    temperature=0,
                ),
            )
        )
        if not response.text:
            raise AIProviderError("Gemini returned an empty extraction response")
        parsed = AIExtractionResponse.model_validate_json(response.text)
        return DrawingExtraction(
            filename=filename,
            drawing_type=parsed.drawing_type,
            rooms=parsed.rooms,
            doors=parsed.doors,
            windows=parsed.windows,
            building_elements=[
                BuildingElement(
                    element_type=element.element_type,
                    quantity=element.quantity,
                    unit=element.unit,
                    source=element.source,
                    confidence=element.confidence,
                )
                for element in parsed.building_elements
            ],
            warnings=parsed.warnings,
        )
    except AIProviderError:
        raise
    except Exception as exc:
        error_text = str(exc)
        if "NOT_FOUND" in error_text or "is not found for API version" in error_text:
            raise AIProviderError(
                f"Gemini model '{settings.model_name}' is unavailable for this API key. "
                "Set MODEL_NAME in .env to a model listed by Google AI Studio, "
                "for example gemini-2.5-flash, then restart Streamlit."
            ) from exc
        raise AIProviderError(f"Gemini extraction failed: {exc}") from exc


def extract_blueprint(filename: str, content: bytes) -> DrawingExtraction:
    """Extract blueprint data with Gemini or validate a local JSON fixture."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".json":
        try:
            payload = json.loads(content.decode("utf-8"))
            return DrawingExtraction.model_validate({"filename": filename, **payload})
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError("Blueprint JSON could not be validated") from exc
    if settings.ai_provider != "gemini":
        raise AIProviderError(
            "AI_PROVIDER is not set to gemini. Configure AI_PROVIDER=gemini and GEMINI_API_KEY in .env."
        )
    return _extract_with_gemini(filename, content)
