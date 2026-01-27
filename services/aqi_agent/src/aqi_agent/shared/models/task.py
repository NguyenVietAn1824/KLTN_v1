from __future__ import annotations

from typing import Any
from typing import Optional

from base import CustomBaseModel as BaseModel
from pydantic import Field


class SubQuestion(BaseModel):
    """Represents a single sub-question within a task.

    A sub-question contains the specific query text, description of what needs
    to be answered, the target table to query, and the resulting data once executed.

    Attributes:
        question (str): The natural language question to be converted to SQL.
            Example: "What is the current AQI in district X?"
        description (str): Detailed description of what the question seeks to answer.
            Helps guide SQL generation with additional context.
        table_name (str | None): The database table to query (e.g., 'distric_stats', 'districts').
            None if table hasn't been determined yet.
        data (dict[str, Any]): The query execution results. Empty dict initially,
            populated after SQL execution with column names as keys.
        sql_query (str): The generated SQL query string. Defaults to empty string
            until the query is built.
    """

    question: str = Field(
        description='The natural language question to be converted to SQL.',
    )
    description: str = Field(
        description='Detailed description of what the question seeks to answer.',
    )
    table_name: str | None = Field(
        default=None,
        description='The database table to query (e.g., distric_stats, districts).',
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description='The query execution results as dictionary.',
    )
    sql_query: str = Field(
        default='',
        description='The generated SQL query string.',
    )


class Task(BaseModel):
    """Represents a collection of related sub-questions that form a task.

    A task groups multiple sub-questions that should be processed together,
    typically representing a logical phase of answering the main question.

    Attributes:
        sub_questions (list[SubQuestion]): List of sub-questions to be processed.
            Can contain 1-3 sub-questions depending on complexity.
    """

    sub_questions: list[SubQuestion] = Field(
        default_factory=list,
        description='List of sub-questions forming this task.',
    )


class TodoList(BaseModel):
    """Complete planning structure containing all tasks for answering a question.

    TodoList represents the decomposed structure of a complex question, broken down
    into sequential tasks. Typically contains 1-2 tasks:
    - first_task: Entity identification or initial data gathering
    - second_task: Data collection with refined context (optional)

    Attributes:
        first_task (Task): The initial task, always present. Usually focuses on
            identifying entities or gathering foundational data.
        second_task (Task | None): Optional follow-up task that uses results from
            first_task to gather additional data with more specific context.
    """

    first_task: Task = Field(
        description='The first task, focusing on entity identification.',
    )
    second_task: Task | None = Field(
        default=None,
        description='Optional second task for data collection with context.',
    )
