"""
Integration tests for PlannerService.

These tests initialize a real LiteLLMService pointing to the local LiteLLM proxy
(http://localhost:9510) and call the PlannerService.process() method with fake inputs.

Run with:
    pytest test/planner/test_service.py -v
    pytest test/planner/test_service.py -v -k "unit"          # unit tests only (no LLM)
    pytest test/planner/test_service.py -v -k "integration"   # integration tests
"""
from __future__ import annotations

import asyncio
import json
import os

import httpx
import pytest
from dotenv import find_dotenv, load_dotenv

from lite_llm import CompletionMessage, LiteLLMService, LiteLLMSetting, MessageRole

# Load project .env so LITELLM__TOKEN etc. are available
load_dotenv(find_dotenv('.env'), override=True)
from aqi_agent.domain.planner.service import (
    PlannerService,
    PlannerServiceInput,
    PlannerServiceOutput,
)
from aqi_agent.domain.planner.models import SubTaskModel
from aqi_agent.shared.settings import PlannerSettings


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


def _log_planner_output(test_name: str, result: PlannerServiceOutput) -> None:
    """Pretty-print the LLM planner output so it's visible in pytest -s."""
    border = '=' * 80
    print(f"\n{border}")
    print(f"  LLM OUTPUT — {test_name}")
    print(border)
    print(f"  requires_clarification : {result.requires_clarification}")
    print(f"  planning_summary       : {result.planning_summary}")
    print(f"  subtasks ({len(result.subtasks)}):")
    for i, st in enumerate(result.subtasks, 1):
        print(f"    [{i}] task_id     : {st.task_id}")
        print(f"        description : {st.description}")
        print(f"        depends_on  : {st.depends_on}")
        print(f"        sql_hint    : {st.sql_hint}")
    print(border + '\n')


def _log_gprocess_output(test_name: str, result: dict) -> None:
    """Pretty-print the gprocess planner state output."""
    border = '=' * 80
    print(f"\n{border}")
    print(f"  GPROCESS OUTPUT — {test_name}")
    print(border)
    ps = result.get('planner_state', {})
    print(f"  requires_clarification : {ps.get('requires_clarification')}")
    print(f"  planning_summary       : {ps.get('planning_summary')}")
    subtasks = ps.get('subtasks', [])
    print(f"  subtasks ({len(subtasks)}):")
    for i, st in enumerate(subtasks, 1):
        print(f"    [{i}] task_id     : {st.get('task_id')}")
        print(f"        description : {st.get('description')}")
        print(f"        depends_on  : {st.get('depends_on')}")
        print(f"        sql_hint    : {st.get('sql_hint')}")
    print(border + '\n')


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
        max_completion_tokens=4096,
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
def planner_settings() -> PlannerSettings:
    """Create PlannerSettings with default values."""
    return PlannerSettings(
        model=LLM_MODEL,
        frequency_penalty=0,
        n=1,
        presence_penalty=0,
        temperature=0,
        top_p=1,
        max_completion_tokens=4096,
    )


@pytest.fixture(scope="module")
def planner_service(
    litellm_service: LiteLLMService,
    planner_settings: PlannerSettings,
) -> PlannerService:
    """Create a PlannerService instance."""
    return PlannerService(
        litellm_service=litellm_service,
        settings=planner_settings,
    )


# ---------------------------------------------------------------------------
# Unit tests (no LLM call)
# ---------------------------------------------------------------------------

class TestSanitize:
    """Unit tests for PlannerService.sanitize() static method."""

    def test_strips_leading_trailing_whitespace(self):
        result = PlannerService.sanitize("  hello world  ")
        assert result == "hello world"

    def test_normalises_double_newlines(self):
        result = PlannerService.sanitize("line1\n\nline2")
        assert result == "line1\nline2"

    def test_returns_empty_string_on_empty_input(self):
        result = PlannerService.sanitize("")
        assert result == ""

    def test_returns_empty_string_on_none(self):
        result = PlannerService.sanitize(None)  # type: ignore[arg-type]
        assert result == ""

    def test_normal_content_unchanged(self):
        content = "What is the AQI in Hanoi today?"
        assert PlannerService.sanitize(content) == content


class TestFormatConversationHistory:
    """Unit tests for PlannerService._format_conversation_history() — no LLM needed."""

    @pytest.fixture()
    def service(self, planner_service: PlannerService) -> PlannerService:
        return planner_service

    def test_empty_history_returns_no_history_message(self, service: PlannerService):
        result = service._format_conversation_history(recent_turns=[])
        assert result == "No recent conversation history."

    def test_formats_turns_with_role_tags(self, service: PlannerService):
        turns = [
            CompletionMessage(role=MessageRole.USER, content="Hello"),
            CompletionMessage(role=MessageRole.ASSISTANT, content="Hi there"),
        ]
        result = service._format_conversation_history(recent_turns=turns)
        assert "<user>Hello</user>" in result
        assert "<assistant>Hi there</assistant>" in result

    def test_multiple_turns_joined_by_newline(self, service: PlannerService):
        turns = [
            CompletionMessage(role=MessageRole.USER, content="Turn 1"),
            CompletionMessage(role=MessageRole.USER, content="Turn 2"),
        ]
        result = service._format_conversation_history(recent_turns=turns)
        lines = result.split("\n")
        assert len(lines) == 2


class TestPlannerServiceInput:
    """Unit tests for PlannerServiceInput model validation."""

    def test_minimal_input(self):
        inp = PlannerServiceInput(rephrased_question="What is AQI?")
        assert inp.rephrased_question == "What is AQI?"
        assert inp.conversation_history == []
        assert inp.conversation_summary == ""
        assert inp.schema == ""
        assert inp.additional_context == ""

    def test_full_input(self):
        inp = PlannerServiceInput(
            rephrased_question="Show AQI for Hoan Kiem",
            conversation_history=[
                CompletionMessage(role=MessageRole.USER, content="Hi"),
            ],
            conversation_summary="Asking about AQI",
            schema="CREATE TABLE districts ...",
            additional_context="Focus on PM2.5",
        )
        assert inp.rephrased_question == "Show AQI for Hoan Kiem"
        assert len(inp.conversation_history) == 1
        assert inp.schema == "CREATE TABLE districts ..."


class TestPlannerServiceOutput:
    """Unit tests for PlannerServiceOutput model defaults."""

    def test_defaults(self):
        out = PlannerServiceOutput()
        assert out.subtasks == []
        assert out.requires_clarification is False
        assert out.planning_summary == ""

    def test_with_subtasks(self):
        subtask = SubTaskModel(
            task_id="t1",
            description="Get AQI data",
            depends_on=[],
            sql_hint="SELECT * FROM aqi",
        )
        out = PlannerServiceOutput(
            subtasks=[subtask],
            requires_clarification=False,
            planning_summary="Simple query plan.",
        )
        assert len(out.subtasks) == 1
        assert out.subtasks[0].task_id == "t1"


# ---------------------------------------------------------------------------
# Integration tests (real LLM call)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.integration
class TestPlannerServiceProcess:
    """Integration tests that call PlannerService.process() against the real LLM."""

    @pytest.fixture(autouse=True)
    async def _throttle(self):
        """Insert a 7-second delay before each test to stay within the 10 rpm
        Google Gemini API rate limit (≈1 request per 6 seconds)."""
        await asyncio.sleep(7)

    async def test_simple_query_decomposition(self, planner_service: PlannerService):
        """A clear query should be decomposed into subtasks without clarification."""
        inputs = PlannerServiceInput(
            rephrased_question="What is the current AQI in Hanoi?",
            conversation_history=[],
            conversation_summary="",
            schema="CREATE TABLE air_quality (id INT, district VARCHAR, aqi INT, timestamp TIMESTAMP);",
        )
        try:
            result = await planner_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        _log_planner_output('test_simple_query_decomposition', result)

        assert isinstance(result, PlannerServiceOutput)
        assert isinstance(result.subtasks, list)
        assert len(result.subtasks) > 0
        assert isinstance(result.requires_clarification, bool)
        assert isinstance(result.planning_summary, str)

    async def test_subtask_structure(self, planner_service: PlannerService):
        """Each subtask should have the expected fields."""
        inputs = PlannerServiceInput(
            rephrased_question="Show the average AQI per district for last month",
            conversation_history=[],
            conversation_summary="",
            schema="CREATE TABLE air_quality (id INT, district VARCHAR, aqi INT, timestamp TIMESTAMP);",
        )
        try:
            result = await planner_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        _log_planner_output('test_subtask_structure', result)

        assert isinstance(result, PlannerServiceOutput)
        for subtask in result.subtasks:
            assert isinstance(subtask, SubTaskModel)
            assert isinstance(subtask.task_id, str) and len(subtask.task_id) > 0
            assert isinstance(subtask.description, str) and len(subtask.description) > 0
            assert isinstance(subtask.depends_on, list)
            assert isinstance(subtask.sql_hint, str)

    async def test_ambiguous_query_requires_clarification(self, planner_service: PlannerService):
        """An ambiguous query with unknown abbreviations should require clarification."""
        inputs = PlannerServiceInput(
            rephrased_question="Tính XYZ cho các quận",
            conversation_history=[],
            conversation_summary="",
            schema="CREATE TABLE air_quality (id INT, district VARCHAR, aqi INT, timestamp TIMESTAMP);",
        )
        try:
            result = await planner_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        _log_planner_output('test_ambiguous_query_requires_clarification', result)

        assert isinstance(result, PlannerServiceOutput)
        assert result.requires_clarification is True

    async def test_clear_query_no_clarification(self, planner_service: PlannerService):
        """A clear standard query should NOT require clarification."""
        inputs = PlannerServiceInput(
            rephrased_question="Show the AQI values for Dong Da district today",
            conversation_history=[],
            conversation_summary="",
            schema="CREATE TABLE air_quality (id INT, district VARCHAR, aqi INT, timestamp TIMESTAMP);",
        )
        try:
            result = await planner_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        _log_planner_output('test_clear_query_no_clarification', result)

        assert isinstance(result, PlannerServiceOutput)
        assert result.requires_clarification is False

    async def test_complex_query_multiple_subtasks(self, planner_service: PlannerService):
        """A complex query should produce multiple subtasks with dependencies."""
        inputs = PlannerServiceInput(
            rephrased_question=(
                "Compare the average AQI between Hoan Kiem and Ba Dinh districts "
                "over the last 7 days and show the daily trend"
            ),
            conversation_history=[],
            conversation_summary="",
            schema=(
                "CREATE TABLE air_quality (id INT, district VARCHAR, aqi INT, "
                "pm25 FLOAT, pm10 FLOAT, timestamp TIMESTAMP);"
            ),
        )
        try:
            result = await planner_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        _log_planner_output('test_complex_query_multiple_subtasks', result)

        assert isinstance(result, PlannerServiceOutput)
        assert len(result.subtasks) >= 1
        assert isinstance(result.planning_summary, str) and len(result.planning_summary) > 0

    async def test_query_with_conversation_history(self, planner_service: PlannerService):
        """A follow-up query with history should use context for planning."""
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
        inputs = PlannerServiceInput(
            rephrased_question="What about the PM2.5 values for the same district?",
            conversation_history=history,
            conversation_summary="User is asking about air quality metrics in Hoan Kiem.",
            schema=(
                "CREATE TABLE air_quality (id INT, district VARCHAR, aqi INT, "
                "pm25 FLOAT, pm10 FLOAT, timestamp TIMESTAMP);"
            ),
        )
        try:
            result = await planner_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        _log_planner_output('test_query_with_conversation_history', result)

        assert isinstance(result, PlannerServiceOutput)
        assert len(result.subtasks) > 0
        assert isinstance(result.requires_clarification, bool)

    async def test_vietnamese_query_planning(self, planner_service: PlannerService):
        """A Vietnamese query should be planned correctly."""
        inputs = PlannerServiceInput(
            rephrased_question="Cho tôi xem chỉ số AQI trung bình theo quận trong tuần qua",
            conversation_history=[],
            conversation_summary="",
            schema=(
                "CREATE TABLE air_quality (id INT, district VARCHAR, aqi INT, "
                "pm25 FLOAT, timestamp TIMESTAMP);"
            ),
        )
        try:
            result = await planner_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        _log_planner_output('test_vietnamese_query_planning', result)

        assert isinstance(result, PlannerServiceOutput)
        assert len(result.subtasks) > 0
        assert result.requires_clarification is False

    async def test_query_without_schema(self, planner_service: PlannerService):
        """A query without schema should still produce a valid output."""
        inputs = PlannerServiceInput(
            rephrased_question="What is the AQI in Hanoi?",
            conversation_history=[],
            conversation_summary="",
            schema="",
        )
        try:
            result = await planner_service.process(inputs)
        except Exception as exc:
            _skip_on_api_error(exc)

        _log_planner_output('test_query_without_schema', result)

        assert isinstance(result, PlannerServiceOutput)
        assert isinstance(result.subtasks, list)


# ---------------------------------------------------------------------------
# gprocess integration test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.integration
class TestPlannerServiceGProcess:
    """Integration tests for the LangGraph wrapper gprocess()."""

    @pytest.fixture(autouse=True)
    async def _throttle(self):
        """Insert a 7-second delay before each test to stay within the 10 rpm
        Google Gemini API rate limit (≈1 request per 6 seconds)."""
        await asyncio.sleep(7)

    async def test_gprocess_returns_planner_state(self, planner_service: PlannerService):
        """gprocess should return a dict with planner_state containing expected keys."""
        state = {
            "question": "What is the AQI in Hanoi right now?",
            "rephrased_state": {
                "rephrased_main_question": "What is the current AQI value in Hanoi?",
                "need_context": True,
                "language": "English",
            },
            "history_retrieval_state": {
                "conversation_summary": "",
                "conversation_memories": [],
            },
            "table_pruner_state": {
                "pruned_schema": "CREATE TABLE air_quality (id INT, district VARCHAR, aqi INT, timestamp TIMESTAMP);",
                "retrieved_tables": [],
                "column_selection": [],
            },
        }
        result = await planner_service.gprocess(state)

        _log_gprocess_output('test_gprocess_returns_planner_state', result)

        assert "planner_state" in result
        planner_state = result["planner_state"]
        assert "subtasks" in planner_state
        assert "requires_clarification" in planner_state
        assert "planning_summary" in planner_state
        assert isinstance(planner_state["subtasks"], list)
        assert len(planner_state["subtasks"]) > 0

    async def test_gprocess_subtask_dict_structure(self, planner_service: PlannerService):
        """Each subtask in gprocess output should be a dict with expected keys."""
        state = {
            "question": "Show average AQI per district",
            "rephrased_state": {
                "rephrased_main_question": "Show the average AQI grouped by district",
                "need_context": True,
                "language": "English",
            },
            "history_retrieval_state": {
                "conversation_summary": "",
                "conversation_memories": [],
            },
            "table_pruner_state": {
                "pruned_schema": "CREATE TABLE air_quality (id INT, district VARCHAR, aqi INT);",
                "retrieved_tables": [],
                "column_selection": [],
            },
        }
        result = await planner_service.gprocess(state)

        _log_gprocess_output('test_gprocess_subtask_dict_structure', result)

        planner_state = result["planner_state"]
        for subtask in planner_state["subtasks"]:
            assert "task_id" in subtask
            assert "description" in subtask
            assert "depends_on" in subtask
            assert "sql_hint" in subtask

    async def test_gprocess_fallback_on_missing_state(self, planner_service: PlannerService):
        """Missing rephrased_state should trigger the fallback plan."""
        state = {
            "question": "What is AQI?",
            # intentionally missing rephrased_state, history_retrieval_state, table_pruner_state
        }
        result = await planner_service.gprocess(state)

        _log_gprocess_output('test_gprocess_fallback_on_missing_state', result)

        assert "planner_state" in result
        planner_state = result["planner_state"]
        assert isinstance(planner_state["subtasks"], list)
        assert isinstance(planner_state["requires_clarification"], bool)
        assert isinstance(planner_state["planning_summary"], str)

    async def test_gprocess_with_conversation_history(self, planner_service: PlannerService):
        """gprocess should handle conversation memories from state."""
        state = {
            "question": "What about Dong Da?",
            "rephrased_state": {
                "rephrased_main_question": "What is the AQI in Dong Da district?",
                "need_context": True,
                "language": "English",
            },
            "history_retrieval_state": {
                "conversation_summary": "User is asking about AQI values in Hanoi districts.",
                "conversation_memories": [
                    {"role": "user", "content": "What is the AQI in Hoan Kiem?"},
                    {"role": "assistant", "content": "The AQI in Hoan Kiem is 152."},
                ],
            },
            "table_pruner_state": {
                "pruned_schema": "CREATE TABLE air_quality (id INT, district VARCHAR, aqi INT);",
                "retrieved_tables": [],
                "column_selection": [],
            },
        }
        result = await planner_service.gprocess(state)

        _log_gprocess_output('test_gprocess_with_conversation_history', result)

        assert "planner_state" in result
        planner_state = result["planner_state"]
        assert len(planner_state["subtasks"]) > 0
