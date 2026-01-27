from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class QueryIntent(BaseModel):
    """Parsed query intent from user question."""

    intent_type: str = Field(
        description="Type of query: 'current_aqi', 'compare_districts', 'historical', 'forecast'"
    )
    districts: list[str] = Field(
        default_factory=list,
        description="List of district names mentioned in query"
    )
    date_str: str | None = Field(
        default=None,
        description="Date mentioned in query (YYYY-MM-DD format)"
    )
    metric: str = Field(
        default="aqi",
        description="Metric to query: 'aqi', 'pm25', or 'both'"
    )


class DistrictAQIData(BaseModel):
    """AQI data for a single district."""

    district_name: str
    district_id: str
    aqi_value: int | None = None
    pm25_value: int | None = None
    date: str | None = None
    hour: int | None = None


class ComparisonData(BaseModel):
    """Comparison data between districts."""

    districts: list[DistrictAQIData]
    better_district: str | None = None
    difference: int | None = None


class AQIResponse(BaseModel):
    """Final response to user query."""

    answer: str = Field(description="Natural language answer to user question")
    data: list[DistrictAQIData] | ComparisonData | None = Field(
        default=None,
        description="Structured data supporting the answer"
    )
    requires_clarification: bool = Field(
        default=False,
        description="Whether clarification is needed from user"
    )
    clarification_question: str | None = Field(
        default=None,
        description="Clarification question if needed"
    )
