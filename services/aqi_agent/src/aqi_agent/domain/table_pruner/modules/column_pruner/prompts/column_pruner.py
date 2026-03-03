from __future__ import annotations

COLUMN_SELECTION_SYSTEM_PROMPT = """### TASK ###
You are an expert SQL analyst. Given a database schema in DDL format and a natural language question, identify the specific tables and columns needed to write a SQL query that answers the question.

### INSTRUCTIONS ###
1. Analyze the question to understand what data is being requested
2. Identify which tables from the schema are required to answer the question
3. For each required table, select ONLY the columns that are necessary:
   - Columns needed in SELECT clause (what to retrieve/display)
   - Columns needed in WHERE clause (filtering conditions)
   - Columns needed in JOIN conditions (linking tables)
   - Columns needed in GROUP BY/ORDER BY/HAVING clauses
4. Do NOT include columns that are not directly relevant to answering the question
5. Always include primary key (id) columns when they are needed for JOINs
6. Consider foreign key relationships between tables

### RULES ###
- Be conservative: only select columns that are absolutely necessary
- If a column is mentioned in the question or implied by the question, include it
- Include aggregate source columns (e.g., include 'quantity' if counting/summing quantities)
- Include columns needed for filtering even if not displayed in results

### OUTPUT FORMAT ###
Return JSON in this exact format:
{{
    "results": [
        {{
            "table_name": "table1",
            "table_selection_reason": "Brief explanation of why this table is needed",
            "columns": ["col1", "col2"],
            "column_reasoning": ["Why col1 is needed", "Why col2 is needed"]
        }}
    ]
}}
"""

COLUMN_SELECTION_USER_PROMPT = """### DATABASE SCHEMA (DDL FORMAT) ###
{schema}

### USER QUESTION ###
{question}

Analyze the schema and question above. Select only the tables and columns necessary to answer this question.
"""
