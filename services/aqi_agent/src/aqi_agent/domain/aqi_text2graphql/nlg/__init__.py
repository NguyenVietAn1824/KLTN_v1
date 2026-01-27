"""
Natural Language Generation (NLG) module for AQI Agent.

This module converts structured query results into natural language answers.
"""

from .service import NLGInput, NLGOutput, NLGService

__all__ = ['NLGInput', 'NLGOutput', 'NLGService']
