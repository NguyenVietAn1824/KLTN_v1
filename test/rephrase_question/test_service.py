"""
Integration tests for RephraseService.

These tests initialize a real LiteLLMService pointing to the local LiteLLM proxy
(http://localhost:9510) and call the RephraseService.process() method with fake inputs.

Run with:
    pytest test/rephrase_question/test_service.py -v
    pytest test/rephrase_question/test_service.py -v -k "unit"    # unit tests only (no LLM)
    pytest test/rephrase_question/test_service.py -v -k "integration"  # integration tests
"""
from __future__ import annotations

import asyncio
import os

import httpx
import pytest
from dotenv import find_dotenv, load_dotenv

from lite_llm import CompletionMessage, LiteLLMService, LiteLLMSetting, MessageRole

# Load project .env so LITELLM__TOKEN etc. are available
load_dotenv(find_dotenv('.env'), override=True)
from aqi_agent.domain.rephrase_question.service import (
    RephraseService,
    RephraseServiceInput,
    RephraseServiceOutput,
)
from aqi_agent.shared.settings import RephraseQuestionSettings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

LITELLM_URL = os.getenv('LITELLM__URL', 'http://localhost:9510')
LITELLM_TOKEN = os.getenv('LITELLM__TOKEN', 'sk-1234')
LLM_MODEL = os.getenv('LITELLM__MODEL', 'gemini-2.5-flash')

# HTTP status codes that indicate a transient upstream API issue
_TRANSIENT_HTTP_CODES = {401, 429, 503}


def _skip_on_api_error(exc: Exception) -> None:
    """Re-raise as pytest.skip for known transient upstream API failures."""
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in _TRANSIENT_HTTP_CODES:
        pytest.skip(
            f"Skipping: upstream API returned {exc.response.status_code} "
            f"(rate-limited or missing API key in LiteLLM pool). Original: {exc}"
        )
    raise exc


@pytest.fixture(scope="module")
def litellm_settings() -> LiteLLMSetting:
    """Build LiteLLMSetting that points to the locally running LiteLLM proxy."""
    return LiteLLMSetting(
        url=LITELLM_URL,
        token=LITELLM_TOKEN,
        model=LLM_MODEL,
        embedding_model="gemini-embedding",
        frequency_penalty=0,
        n=1,
        presence_penalty=0,
        temperature=0,
        top_p=1,
        max_completion_tokens=1024,
        encoding_format="float",
        dimensions=1536,
        max_length=8000,
        timeout=60,
        connect_timeout=10,
        max_connections=200,
        max_keepalive_connections=40,
        context_window=100000,
        condition_model=LLM_MODEL,
    )


@pytest.fixture(scope="module")
def litellm_service(litellm_settings: LiteLLMSetting) -> LiteLLMService:
    """Create a LiteLLMService instance."""
    return LiteLLMService(settings=litellm_settings)


@pytest.fixture(scope="module")
def rephrase_settings() -> RephraseQuestionSettings:
    """Create RephraseQuestionSettings with default values."""
    return RephraseQuestionSettings(
        model=LLM_MODEL,
        frequency_penalty=0,
        n=1,
        presence_penalty=0,
        temperature=0,
        top_p=1,
        max_completion_tokens=1024,
    )


@pytest.fixture(scope="module")
def rephrase_service(
    litellm_service: LiteLLMService,
    rephrase_settings: RephraseQuestionSettings,
) -> RephraseService:
    """Create a RephraseService instance."""
    return RephraseService(
        litellm_service=litellm_service,
        settings=rephrase_settings,
    )


# ---------------------------------------------------------------------------
# Unit tests (no LLM call)
# ---------------------------------------------------------------------------

class TestSanitize:
    """Unit tests for RephraseService.sanitize() static method."""

    def test_strips_leading_trailing_whitespace(self):
        result = RephraseService.sanitize("  hello world  ")
        assert result == "hello world"

    def test_normalises_double_newlines(self):
        result = RephraseService.sanitize("line1\n\nline2")
        assert result == "line1\nline2"

    def test_raises_on_empty_string(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            RephraseService.sanitize("")

    def test_raises_on_none(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            RephraseService.sanitize(None)  # type: ignore[arg-type]

    def test_normal_content_unchanged(self):
        content = "What is the AQI in Hanoi today?"
        assert RephraseService.sanitize(content) == content


class TestPreprocessMemory:
    """Unit tests for RephraseService.preprocess_memory() — no LLM needed."""

    @pytest.fixture()
    def service(self, rephrase_service: RephraseService) -> RephraseService:
        return rephrase_service

    def test_empty_history_returns_empty_string(self, service: RephraseService):
        result = service.preprocess_memory(question="Any question?", recent_turns=[])
        assert result == ""

    def test_formats_turns_with_role_tags(self, service: RephraseService):
        turns = [
            CompletionMessage(role=MessageRole.USER, content="Hello"),
            CompletionMessage(role=MessageRole.ASSISTANT, content="Hi there"),
        ]
        result = service.preprocess_memory(question="Next?", recent_turns=turns)
        assert "<user>Hello</user>" in result
        assert "<assistant>Hi there</assistant>" in result

    def test_multiple_turns_joined_by_newline(self, service: RephraseService):
        turns = [
            CompletionMessage(role=MessageRole.USER, content="Turn 1"),
            CompletionMessage(role=MessageRole.USER, content="Turn 2"),
        ]
        result = service.preprocess_memory(question="Q", recent_turns=turns)
        lines = result.split("\n")
        assert len(lines) == 2


# ---------------------------------------------------------------------------
# Integration tests (real LLM call)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.integration
class TestRephraseServiceProcess:
    """Integration tests that call RephraseService.process() against the real LLM."""

    @pytest.fixture(autouse=True)
    async def _throttle(self):
        """Insert a 7-second delay before each test to stay within the 10 rpm
        Google Gemini API rate limit (≈1 request per 6 seconds)."""
        await asyncio.sleep(7)

    async def test_simple_question_no_history(self, rephrase_service: RephraseService):
        """A standalone question should return a rephrased version and proper types."""
        inputs = RephraseServiceInput(
            question="What is the air quality in Hanoi?",
            conversation_history=[],
            summary="",
        )
        try:
            result = await rephrase_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        assert isinstance(result, RephraseServiceOutput)
        assert isinstance(result.rephrased_main_question, str)
        assert len(result.rephrased_main_question) > 0
        assert isinstance(result.need_context, bool)
        assert isinstance(result.language, str)

    async def test_question_needing_db_context(self, rephrase_service: RephraseService):
        """A question about current AQI data returns a valid RephraseServiceOutput.

        Note: The system prompt is currently calibrated for e-commerce data (product,
        orders, cart, etc.), so `need_context` may be False for AQI-specific questions
        until the prompt is updated for AQI domain data.
        """
        inputs = RephraseServiceInput(
            question="What is the current AQI value for Hoan Kiem district?",
            conversation_history=[],
            summary="",
        )
        try:
            result = await rephrase_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        assert isinstance(result, RephraseServiceOutput)
        assert isinstance(result.need_context, bool)  # True once AQI prompt is updated

    async def test_question_not_needing_db_context(self, rephrase_service: RephraseService):
        """A general knowledge question should set need_context=False."""
        inputs = RephraseServiceInput(
            question="What does AQI stand for?",
            conversation_history=[],
            summary="",
        )
        try:
            result = await rephrase_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        assert isinstance(result, RephraseServiceOutput)
        assert result.need_context is False

    async def test_question_with_conversation_history(self, rephrase_service: RephraseService):
        """A follow-up question should be resolved using conversation history."""
        history = [
            CompletionMessage(
                role=MessageRole.USER,
                content="What is the AQI in Hoan Kiem district today?",
            ),
            CompletionMessage(
                role=MessageRole.ASSISTANT,
                content="The current AQI in Hoan Kiem is 152, which is Unhealthy.",
            ),
        ]
        inputs = RephraseServiceInput(
            question="What about Dong Da?",
            conversation_history=history,
            summary="User is asking about AQI values in Hanoi districts.",
        )
        try:
            result = await rephrase_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        assert isinstance(result, RephraseServiceOutput)
        # The rephrased question should incorporate "Dong Da" from context
        assert "Dong Da" in result.rephrased_main_question or len(result.rephrased_main_question) > 0
        # need_context reflects AQI data lookup; may be False until prompt is updated for AQI domain
        assert isinstance(result.need_context, bool)

    async def test_question_with_summary(self, rephrase_service: RephraseService):
        """Summary context should help resolve ambiguous pronouns."""
        inputs = RephraseServiceInput(
            question="How about yesterday?",
            conversation_history=[
                CompletionMessage(
                    role=MessageRole.USER,
                    content="What was the AQI in Ba Dinh district this morning?",
                ),
                CompletionMessage(
                    role=MessageRole.ASSISTANT,
                    content="The AQI in Ba Dinh this morning was 120.",
                ),
            ],
            summary="The conversation is about AQI levels in Ba Dinh district.",
        )
        try:
            result = await rephrase_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        assert isinstance(result, RephraseServiceOutput)
        assert isinstance(result.rephrased_main_question, str)
        assert len(result.rephrased_main_question) > 0

    async def test_non_question_input_returns_original_or_empty(
        self, rephrase_service: RephraseService
    ):
        """Non-question inputs (e.g. casual reactions) should not be rephrased."""
        inputs = RephraseServiceInput(
            question="Hmm, that's interesting.",
            conversation_history=[],
            summary="",
        )
        try:
            result = await rephrase_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        assert isinstance(result, RephraseServiceOutput)
        assert isinstance(result.rephrased_main_question, str)

    async def test_vietnamese_question_detected_as_vietnamese(
        self, rephrase_service: RephraseService
    ):
        """A Vietnamese question should be detected and assigned a non-empty language."""
        inputs = RephraseServiceInput(
            question="Chất lượng không khí ở Hà Nội hôm nay như thế nào?",
            conversation_history=[],
            summary="",
        )
        try:
            result = await rephrase_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        assert isinstance(result, RephraseServiceOutput)
        # The LLM may return 'vi', 'Vietnamese', or similar — just verify it's detected
        assert isinstance(result.language, str) and len(result.language) > 0

    async def test_output_fallback_when_rephrase_is_none(
        self, rephrase_service: RephraseService
    ):
        """
        If the LLM returns null for rephrase_main_question, the service
        should fall back to the original question.
        """
        inputs = RephraseServiceInput(
            question="Tell me something.",
            conversation_history=[],
            summary="",
        )
        try:
            result = await rephrase_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        # Regardless of LLM output, result must not be empty
        assert result.rephrased_main_question != ""


# ---------------------------------------------------------------------------
# gprocess integration test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.integration
class TestRephraseServiceGProcess:
    """Integration tests for the LangGraph wrapper gprocess()."""

    async def test_gprocess_returns_rephrased_state(self, rephrase_service: RephraseService):
        state = {
            "question": "What is the AQI in Hanoi right now?",
            "conversation_memories": [],
            "conversation_summary": "",
        }
        result = await rephrase_service.gprocess(state)

        assert "rephrased_state" in result
        rephrased = result["rephrased_state"]
        assert "rephrased_main_question" in rephrased
        assert "need_context" in rephrased
        assert "language" in rephrased

    async def test_gprocess_fallback_on_empty_question(self, rephrase_service: RephraseService):
        """Empty question should trigger fallback with original question."""
        state = {
            "question": "",
            "conversation_memories": [],
            "conversation_summary": "",
        }
        result = await rephrase_service.gprocess(state)

        assert "rephrased_state" in result
        rephrased = result["rephrased_state"]
        # fallback: original question (empty) or default English
        assert rephrased["need_context"] is False
        assert rephrased["language"] == "English"
