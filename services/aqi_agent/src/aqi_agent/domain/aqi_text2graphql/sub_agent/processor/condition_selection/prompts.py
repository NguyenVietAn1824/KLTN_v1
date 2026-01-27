"""
Condition selection prompts for KLTN AQI system.

These prompts guide the LLM to generate QueryConstraints (WHERE, ORDER BY, LIMIT).
"""

CONDITION_SELECTION_SYSTEM_PROMPT = """You are an expert at generating GraphQL query constraints (WHERE clauses, ORDER BY, LIMIT) based on user questions about air quality.

Your task is to analyze the user's question and the selected fields, then generate appropriate query constraints.

**Available Operators (Op enum):**
- "_eq": Equal to (exact match)
- "_neq": Not equal to
- "_gt": Greater than
- "_gte": Greater than or equal to
- "_lt": Less than
- "_lte": Less than or equal to
- "_in": Value in array [val1, val2, ...]
- "_nin": Value not in array
- "_between": Value between [low, high]
- "_like": SQL LIKE pattern (case-sensitive) - use % wildcards
- "_ilike": SQL ILIKE pattern (case-insensitive) - use % wildcards
- "_is_null": Field is null (value should be true)
- "_is_not_null": Field is not null (value should be true)

**Boolean Logic:**
- Use "_and" for conditions that must ALL be true: {{"_and": [cond1, cond2]}}
- Use "_or" for conditions where AT LEAST ONE must be true: {{"_or": [cond1, cond2]}}
- Use "_not" to negate a condition: {{"_not": condition}}
- Simple conditions: {{"field": "aqi", "op": "_gt", "value": 100}}

**CRITICAL: Hasura Relationship Filters (NEW!):**
- Tables have relationships: distric_stats ↔ districts
- Can filter on related table fields using nested conditions!
- **For filtering distric_stats by district NAME:**
  ```
  where: {{
    "field": "district",  // Relationship field name
    "nested": {{
      "field": "name",
      "op": "_ilike",
      "value": "%Ba Đình%"
    }}
  }}
  ```
- This generates: `where: {{district: {{name: {{_ilike: "%Ba Đình%"}}}}}}`
- **ALWAYS use relationship filters when filtering by district name in distric_stats table!**

**Query Structure:**
{{
  "where": <BoolExpr or null>,  // Filtering conditions (can include nested relationship filters!)
  "order_by": [{{"field": "aqi", "dir": "desc", "nulls": null}}],  // Sorting
  "limit": 10,  // Max results
  "offset": 0   // Skip results (for pagination)
}}

**Common Patterns:**

0. **Filtering by district NAME (using relationship) - MOST COMMON:**
   - Question: "AQI hiện tại ở Ba Đình"
   - Table: distric_stats
   - where: {{"field": "district", "nested": {{"field": "name", "op": "_ilike", "value": "%Ba Đình%"}}}}
   - order_by: [{{"field": "date", "dir": "desc"}}, {{"field": "hour", "dir": "desc"}}]
   - limit: 1
   - **CRITICAL:** When querying distric_stats for a specific district, ALWAYS use nested relationship filter!

1. **Current/Latest data:**
   - Question: "Current AQI in district X"
   - where: See pattern 0 above for district filtering
   - order_by: [{{"field": "date", "dir": "desc"}}, {{"field": "hour", "dir": "desc"}}]
   - limit: 1

2. **Historical/Date-based:**
   - Question: "AQI in Ba Đình on 2024-01-15"
   - where: {{"_and": [
       {{"field": "district", "nested": {{"field": "name", "op": "_ilike", "value": "%Ba Đình%"}}}},
       {{"field": "date", "op": "_eq", "value": "2024-01-15"}}
     ]}}
   
3. **Comparison/Range:**
   - Question: "Districts with AQI over 100"
   - where: {{"field": "aqi_value", "op": "_gt", "value": 100}}
   - order_by: [{{"field": "aqi_value", "dir": "desc"}}]

4. **Top N:**
   - Question: "Top 5 most polluted districts"
   - where: null
   - order_by: [{{"field": "aqi_value", "dir": "desc"}}]
   - limit: 5

**Guidelines:**
- For "current"/"latest": Use ORDER BY date/time DESC + LIMIT 1
- For district names: Use "_ilike" with "%" wildcards for flexible matching
- For date filters: Use "_eq" for exact dates, "_between" for ranges
- For AQI thresholds: Use "_gt", "_gte", "_lt", "_lte"
- Return null for any field if no constraint is needed
- Be conservative: Don't add constraints unless clearly needed

**Today's date:** {today}
"""

CONDITION_SELECTION_USER_PROMPT = """Based on the user's question and selected fields, generate appropriate query constraints.

Question: {question}
Task Description: {description}
Selected Fields: {context}

Generate QueryConstraints with:
- where: Filtering conditions (or null if no filtering needed)
- order_by: Sorting (or null if no sorting needed)  
- limit: Number of results to return (or null for all)
- offset: Number to skip (or null for none)

For "current AQI" queries: Use ORDER BY date DESC, hour DESC LIMIT 1
"""
