from __future__ import annotations

from typing import Any
from typing import TypedDict

from .model.planning import TodoList


class AQIAgentState(TypedDict, total=False):
    """State definition for AQI Agent LangGraph workflow.

    This TypedDict defines all state variables that flow through the agentic workflow.
    The workflow progresses through planning, SQL generation, and execution phases,
    with state being updated at each node.

    Attributes:
        raw_question (str): The original user question about air quality.
            Example: "What is the AQI in Hoan Kiem district today?"
        context_schema (dict[str, str]): Table name to description mapping for planning.
            Example: {'distric_stats': 'Contains AQI data...', 'districts': 'District metadata...'}
        shared_memory (TodoList | None): The planning structure containing tasks and
            sub-questions. Generated in planning phase, updated during execution.
        _task_number (int): Total number of tasks in the plan (1 or 2). Used to
            control workflow loops.
        _task_idx (int): Current task index being processed (1-based). Increments
            after each task completion to control loop progression.
        exception (dict[str, Any] | None): Error information if processing fails.
            Contains 'where' (error location) and 'error' (error message) keys.
        response_time (float): Total processing time in seconds. Updated at end.
        final_answer (str | None): The natural language answer to the user's question,
            formatted from query results.
        requires_human_intervention (bool): Flag indicating if human input is needed.
            Set to True when clarification is required.
        clarification_question (str | None): Question to ask user if intervention needed.
    """

    raw_question: str
    context_schema: dict[str, str]
    shared_memory: TodoList | None
    _task_number: int
    _task_idx: int
    exception: dict[str, Any] | None
    response_time: float
    final_answer: str | None
    requires_human_intervention: bool
    clarification_question: str | None


class SubAgentState(TypedDict, total=False):
    """State definition for sub-question processing within a task.

    This state flows through the SQL generation pipeline: field selection,
    condition generation, query building, and execution.

    Attributes:
        question (str): The sub-question to be converted to SQL.
        description (str): Additional context describing what to answer.
        table_name (str): The target database table for the query.
        shared_memory (TodoList): Results from previous tasks, used for query refinement.
        task_idx (int): Current task index (1 or 2).
        schema_context (dict[str, Any]): Database schema information for the target table.
            Includes column names, types, descriptions, and relationships.
        selected_fields (list[str]): Fields to SELECT in the SQL query.
        conditions (dict[str, Any]): Query constraints (WHERE, ORDER BY, LIMIT, etc.).
        sql_query (str): The generated SQL query string.
        data (dict[str, Any]): Query execution results.
        exception (dict[str, Any] | None): Error information if processing fails.
    """

    question: str
    description: str
    table_name: str
    shared_memory: TodoList
    task_idx: int
    schema_context: dict[str, Any]
    selected_fields: list[str]
    conditions: dict[str, Any]
    sql_query: str
    data: dict[str, Any]
    exception: dict[str, Any] | None
