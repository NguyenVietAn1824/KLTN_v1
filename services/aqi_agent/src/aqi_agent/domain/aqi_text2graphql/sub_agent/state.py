"""
Sub-Agent state for AQI Text2GraphQL workflow.

Defines the state structure used in LangGraph workflow.
"""

from typing import Any, Dict, List, Optional, TypedDict

from aqi_agent.shared.model import QueryConstraints


class SubAgentState(TypedDict, total=False):
    """
    State for Sub-Agent LangGraph workflow.
    
    This state is passed between nodes in the workflow.
    Each node reads from and writes to this state.
    """
    
    # Input
    question: str  # User's question
    description: str  # Task description
    table_name: str  # Target table
    
    # Field Selection
    fields: Optional[List[Dict[str, Any]]]  # Selected fields
    
    # Condition Selection
    conditions: Optional[QueryConstraints]  # WHERE, ORDER BY, LIMIT
    
    # Query Building
    query: str  # GraphQL query string
    
    # Execution
    data: Optional[Dict[str, Any]]  # Query results
    error: Optional[str]  # Error message if any
