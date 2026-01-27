"""
Planning models for query decomposition.

Adapted from sun_assistant Apollo for KLTN AQI system.
Used by Planning Service to break down complex questions into sub-queries.
"""

from typing import Any, Dict, List, Optional

from base import BaseModel
from pydantic import Field


class SubQuestion(BaseModel):
    """
    A sub-question that queries a specific table.
    
    CRITICAL: Each sub-question has its own table_name!
    Multiple sub-questions in same task can query different tables.
    """
    
    question: str = Field(
        description="The sub-question to be answered. Should be specific and focused. "
                    "Example: 'What is the district ID for Ba Dinh?'"
    )
    
    description: str = Field(
        description="Why this sub-question needs to be answered. "
                    "Example: 'Need district ID to query AQI data from distric_stats'"
    )
    
    table_name: str = Field(
        description="Which database table to query for THIS sub-question. "
                    "Options: 'districts', 'distric_stats', 'air_component', 'provinces'. "
                    "CRITICAL: Each sub-question can query a different table!"
    )
    
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Query results will be stored here after execution. Initially empty {}."
    )
    
    query: str = Field(
        default='',
        description="Generated GraphQL query string. Initially empty."
    )


class Task(BaseModel):
    """
    A single task containing multiple sub-questions that can run in parallel.
    
    CRITICAL DIFFERENCE FROM OLD MODEL:
    - NO table_name at task level
    - Each sub_question has its own table_name
    - Multiple sub-questions can query different tables in parallel
    
    Example: For "What is AQI in Ba Dinh?":
    - SubQuestion 1: Query districts table for district ID (table_name='districts')
    - SubQuestion 2: Query distric_stats for AQI data (table_name='distric_stats')
    Both run in parallel in same task!
    """
    
    sub_questions: List[SubQuestion] = Field(
        description="List of sub-questions to execute in parallel. "
                    "Each has its own table_name. Can query multiple tables."
    )


class TodoList(BaseModel):
    """
    Complete plan for answering the user's question.
    
    Following Apollo architecture:
    - first_task: Always exists, contains initial data collection sub-questions
    - second_task: Optional, for dependent queries that need first_task results
    
    Example workflow:
    Question: "What is current AQI in Ba Dinh district?"
    
    first_task:
      sub_questions:
        1. Query districts for "Ba Dinh" district_id (table_name='districts')
        2. Query distric_stats for latest AQI (table_name='distric_stats')
    
    second_task: null (not needed, can combine results from first_task)
    """
    
    first_task: Task = Field(
        description="Primary task with sub-questions for initial data collection. "
                    "MUST always exist. Sub-questions run in parallel."
    )
    
    second_task: Optional[Task] = Field(
        default=None,
        description="Optional secondary task for dependent queries. "
                    "Only use if second set of queries DEPENDS on first_task results. "
                    "Example: After identifying user in first_task, query their projects in second_task."
    )
