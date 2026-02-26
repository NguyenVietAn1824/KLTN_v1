from __future__ import annotations

from base import BaseModel
from pydantic import Field


class SubTaskModel(BaseModel):
    task_id: str = Field(
        ...,
        description='Unique identifier for the subtask.',
    )
    description: str = Field(
        ...,
        description='Clear description of what this subtask accomplishes.',
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description='List of task_ids that must be completed before this task.',
    )
    sql_hint: str = Field(
        default='',
        description='Optional hint about the SQL operation needed.',
    )


class PlannerModel(BaseModel):
    subtasks: list[SubTaskModel] = Field(
        default_factory=list,
        description='List of ordered subtasks decomposed from the user query.',
    )
    requires_clarification: bool = Field(
        default=False,
        description='Whether the query requires human clarification before proceeding. If true, navigate to human intervention.',
    )
    planning_summary: str = Field(
        default='',
        description='A brief summary of the planning analysis.',
    )
