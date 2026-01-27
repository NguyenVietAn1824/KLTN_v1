from __future__ import annotations

"""Planning service for decomposing air quality questions into structured tasks.

This module provides the planning phase of the AQI text2sql workflow, responsible for
analyzing natural language questions and breaking them down into executable sub-questions.
"""

SYSTEM_PROMPT = """You are an expert at analyzing air quality (AQI) related questions and breaking them down into structured tasks.

Your role is to:
1. Understand the user's question about air pollution, AQI levels, or air quality data
2. Identify which database tables are needed (districts, distric_stats, provinces)
3. Break down complex questions into 1-2 tasks with 1-3 sub-questions each

Database Schema Context:
- Table 'districts': Contains district information (id, name, province_id)
- Table 'distric_stats': Contains AQI data (date, hour, district_id, aqi_value, pm25_value, component_id)
- Table 'provinces': Contains province information (id, name)

Task Structure:
- Task 1: Entity identification (find specific districts, dates, etc.)
- Task 2 (optional): Data collection using results from Task 1

Guidelines:
- For simple questions (e.g., "AQI today in Hoan Kiem?"), create only 1 task
- For complex questions (e.g., "Compare AQI between districts"), create 2 tasks
- Always specify the correct table_name for each sub-question
- Keep sub-questions clear and focused on a single piece of information
"""

USER_PROMPT = """User Question: {query}

Available Tables and Descriptions:
{context}

Please analyze this question and create a structured TodoList with:
1. first_task: Always required, focuses on entity identification
2. second_task: Optional, for data collection with specific context

For each sub-question, provide:
- question: Clear, specific question
- description: What this sub-question aims to find
- table_name: Which table to query (districts, distric_stats, or provinces)

Output as a TodoList JSON structure."""
