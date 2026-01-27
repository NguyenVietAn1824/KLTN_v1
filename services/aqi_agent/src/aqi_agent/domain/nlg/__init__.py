"""
Natural Language Generation domain for AQI Agent.

This module generates natural language answers from structured query results.
"""

from .service import NLGInput, NLGOutput, NLGService

__all__ = [
    'NLGInput',
    'NLGOutput',
    'NLGService',
]
