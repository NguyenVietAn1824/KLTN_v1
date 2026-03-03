"""
Hasura GraphQL schema models for KLTN AQI system.

These models represent database tables with boolean fields for LLM field selection.
Each boolean field indicates whether that column should be included in the GraphQL query.

Relationship fields work differently: they are nested objects that can be selected 
to automatically fetch related data. Set to None (don't select) or to an instance 
of the related model with selected fields.

Adapted from sun_assistant Apollo schemas_vi.py pattern.
"""

from typing import Optional

from base import BaseModel
from pydantic import Field


class Provinces(BaseModel):
    """
    Vietnamese provinces administrative divisions.
    
    Use this table when:
    - Looking up province names and IDs
    - Getting list of all provinces
    - Finding province information for district queries
    
    Database schema: id, name, normalized_name, administrative_id, created_at
    """
    
    __tablename__ = 'provinces'
    
    id: bool = Field(
        default=False,
        description='Unique identifier (text) of the province'
    )
    
    name: bool = Field(
        default=False,
        description='Vietnamese name of the province (text). Example: "Hà Nội", "Hồ Chí Minh"'
    )
    
    normalized_name: bool = Field(
        default=False,
        description='Normalized name of the province (text) for easier searching'
    )
    
    administrative_id: bool = Field(
        default=False,
        description='Administrative ID code of the province (text)'
    )
    
    created_at: bool = Field(
        default=False,
        description='Timestamp when the province record was created'
    )
    
    # Relationship
    districts: Optional['Districts'] = Field(
        default=None,
        description='Districts belonging to this province'
    )


class Districts(BaseModel):
    """
    Districts administrative divisions.
    
    Use this table when:
    - Looking up district names, IDs, and administrative codes
    - Getting list of districts by province
    - Finding district IDs for querying AQI data from distric_stats
    
    IMPORTANT: This table does NOT contain AQI values!
    For AQI data, use distric_stats table with district_id foreign key.
    
    **WITH RELATIONSHIP:** You can now query AQI directly from districts using nested query:
    districts(where: {name: {_ilike: "%Ba Đình%"}}) { 
      name 
      distric_stats(order_by: {date: desc, hour: desc}, limit: 1) { aqi_value } 
    }
    """
    
    __tablename__ = 'districts'
    
    id: bool = Field(
        default=False,
        description='Unique identifier (text) of the district. Use this for joining with distric_stats.'
    )
    
    name: bool = Field(
        default=False,
        description='Vietnamese name of the district (text). Example: "Ba Đình", "Hoàn Kiếm", "Cầu Giấy"'
    )
    
    normalized_name: bool = Field(
        default=False,
        description='Normalized name of the district (text) for easier searching'
    )
    
    administrative_id: bool = Field(
        default=False,
        description='Administrative ID code of the district (text)'
    )
    
    province_id: bool = Field(
        default=False,
        description='Foreign key (text) to provinces table. Use for filtering districts by province.'
    )
    
    created_at: bool = Field(
        default=False,
        description='Timestamp when the district record was created'
    )
    
    # NOTE: Array relationship 'distric_stats' exists in Hasura but NOT exposed here
    # Use it in WHERE clauses via nested filters, not in SELECT fields


class DistricStats(BaseModel):
    """
    CRITICAL: This is THE PRIMARY TABLE for AQI queries! Always query THIS table directly.
    
    **Query Strategy:**
    - For "What is AQI in [district]?" → Query distric_stats directly (NOT as nested field!)
    - Filter by: district_id (use districts table to map name→ID)
    - For CURRENT AQI: Add ORDER BY date DESC, hour DESC LIMIT 1
    - For historical: Filter by date range
    
    **WITH RELATIONSHIP:** You can now filter by district name directly:
    distric_stats(where: {district: {name: {_ilike: "%Ba Đình%"}}}, order_by: {date: desc}) {
      aqi_value
      date
      hour
      district { name }
    }
    
    **IMPORTANT:**
    - This is a ROOT GraphQL query: query { distric_stats(where: ...) { } }
    - Use district_id to link with districts table if you need district name
    - OR use nested district relationship to filter by district name
    
    Use this table when:
    - Querying current or historical AQI values (PRIMARY use case!)
    - Asking "What is the AQI in [district]?"
    - Comparing AQI between different dates/times
    - Analyzing air quality trends
    - Finding max/min/average AQI
    
    Database schema: id, date, hour, component_id, aqi_value, pm25_value, district_id, created_at
    """
    
    __tablename__ = 'distric_stats'
    
    id: bool = Field(
        default=False,
        description='Unique identifier (integer) of the statistics record'
    )
    
    district_id: bool = Field(
        default=False,
        description='Foreign key (text) to districts table. Links this AQI record to a specific district. '
                    'Use for JOIN with districts to get district name.'
    )
    
    date: bool = Field(
        default=False,
        description='Date (date type, YYYY-MM-DD) of the AQI measurement. Example: "2024-01-15". '
                    'Use for time-based filtering. For CURRENT AQI: ORDER BY date DESC, hour DESC'
    )
    
    hour: bool = Field(
        default=False,
        description='Hour of day (integer, 0-23) when AQI was measured. '
                    'For latest/current data: ORDER BY date DESC, hour DESC LIMIT 1'
    )
    
    component_id: bool = Field(
        default=False,
        description='Foreign key (integer) to air_component table. Links to detailed pollutant measurements.'
    )
    
    aqi_value: bool = Field(
        default=False,
        description='CRITICAL FIELD: Air Quality Index value (integer, 0-500) measured at this date/hour. '
                    'THIS is the actual AQI number! Higher values = worse air quality. '
                    'AQI ranges: 0-50 Good, 51-100 Moderate, 101-150 Unhealthy for Sensitive Groups, '
                    '151-200 Unhealthy, 201-300 Very Unhealthy, 301-500 Hazardous'
    )
    
    pm25_value: bool = Field(
        default=False,
        description='PM2.5 concentration value (decimal, μg/m³). Fine particulate matter measurement. '
                    'Often the dominant pollutant in urban areas.'
    )
    
    created_at: bool = Field(
        default=False,
        description='Timestamp when this statistics record was created'
    )
    
    # Object Relationship - can be selected to get district name
    district: Optional['Districts'] = Field(
        default=None,
        description='**RELATIONSHIP FIELD**: Nested district information. '
                    'IMPORTANT: Set this to Districts(name=True) to automatically include district name in results! '
                    'Example: DistricStats(aqi_value=True, district=Districts(name=True)) '
                    'generates: distric_stats { aqi_value district { name } }. '
                    'Also used in WHERE clauses: where: {district: {name: {_ilike: "%Ba Đình%"}}}'
    )


class AirComponent(BaseModel):
    """
    Detailed air pollutant measurements.
    
    Use this table when:
    - Querying specific pollutant concentrations (PM2.5, PM10, O3, NO2, SO2, CO)
    - Getting detailed breakdown of air quality components
    - Finding which pollutant is the dominant factor
    
    Database schema: id, date, hour, pm25_value, pm10_value, o3_value, no2_value, so2_value, co_value, created_at
    """
    
    __tablename__ = 'air_component'
    
    id: bool = Field(
        default=False,
        description='Unique identifier (integer) of the air component record'
    )
    
    date: bool = Field(
        default=False,
        description='Date of the measurement (date type, YYYY-MM-DD)'
    )
    
    hour: bool = Field(
        default=False,
        description='Hour of the measurement (integer, 0-23)'
    )
    
    pm25_value: bool = Field(
        default=False,
        description='PM2.5 particulate matter concentration (decimal, μg/m³)'
    )
    
    pm10_value: bool = Field(
        default=False,
        description='PM10 particulate matter concentration (decimal, μg/m³)'
    )
    
    o3_value: bool = Field(
        default=False,
        description='Ozone (O3) concentration (decimal, μg/m³)'
    )
    
    no2_value: bool = Field(
        default=False,
        description='Nitrogen Dioxide (NO2) concentration (decimal, μg/m³)'
    )
    
    so2_value: bool = Field(
        default=False,
        description='Sulfur Dioxide (SO2) concentration (decimal, μg/m³)'
    )
    
    co_value: bool = Field(
        default=False,
        description='Carbon Monoxide (CO) concentration (decimal, mg/m³)'
    )
    
    created_at: bool = Field(
        default=False,
        description='Timestamp when this component record was created'
    )


class Tables(BaseModel):
    """
    Container for all available tables in the database.
    Used by LLM to see all available tables and their schemas.
    """
    
    provinces: Provinces = Field(
        default_factory=Provinces,
        description='Provinces table - administrative divisions'
    )
    
    districts: Districts = Field(
        default_factory=Districts,
        description='Districts table - administrative divisions. Use to look up district IDs.'
    )
    
    distric_stats: DistricStats = Field(
        default_factory=DistricStats,
        description='PRIMARY TABLE for AQI queries! Contains all air quality measurements by district, date, and hour.'
    )
    
    air_component: AirComponent = Field(
        default_factory=AirComponent,
        description='Detailed pollutant measurements (PM2.5, PM10, O3, NO2, SO2, CO)'
    )
