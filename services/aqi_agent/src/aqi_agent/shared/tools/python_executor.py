from __future__ import annotations

import math
import re
from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import Any

from logger import get_logger
from simpleeval import SimpleEval

logger = get_logger(__name__)


class PythonExecutor:
    """Utility class for safely executing Python expressions in SQL queries.

    Provides methods to evaluate Python code within <python> tags in SQL queries
    and replace them with their computed results. Uses SimpleEval for safe execution.
    """

    PYTHON_TAG_PATTERN = re.compile(r'<python>(.*?)</python>', re.DOTALL)

    SAFE_NAMES = {
        'pi': math.pi,
        'e': math.e,
        'tau': math.tau,
    }

    SAFE_FUNCTIONS = {
        'datetime': datetime,
        'date': date,
        'timedelta': timedelta,

        'abs': abs,
        'min': min,
        'max': max,
        'round': round,
        'sum': sum,
        'int': int,
        'float': float,
        'str': str,
    }

    SAFE_FUNCTIONS.update({
        name: getattr(math, name)
        for name in dir(math)
        if not name.startswith('_') and callable(getattr(math, name))
    })

    @staticmethod
    def execute_python_code(code: str) -> Any:
        """Execute Python code safely using SimpleEval with extended capabilities."""
        if not code.strip():
            return ''

        try:
            if not SimpleEval:
                raise RuntimeError('simpleeval is not installed')

            s_eval = SimpleEval()
            s_eval.names = PythonExecutor.SAFE_NAMES.copy()
            s_eval.functions = PythonExecutor.SAFE_FUNCTIONS.copy()

            result = s_eval.eval(code)
            logger.debug(f'Python code executed successfully: {code} -> {result}')
            return result
        except Exception as e:
            logger.error(f'Error executing Python code: {e}')
            raise ValueError(f'Failed to execute Python code: {str(e)}')

    @staticmethod
    def process_sql_with_python_tags(sql_query: str) -> str:
        """Process SQL query by finding and evaluating <python> tags."""
        def replace_python_tag(match):
            python_code = match.group(1).strip()

            try:
                result = PythonExecutor.execute_python_code(python_code)

                if isinstance(result, (datetime, date)):
                    result_str = result.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    result_str = str(result)

                return result_str
            except ValueError as e:
                logger.warning(f'Python execution error: {e}')
                return match.group(0)

        try:
            processed_sql = PythonExecutor.PYTHON_TAG_PATTERN.sub(
                replace_python_tag, sql_query,
            )
            return processed_sql
        except Exception as e:
            logger.exception(f'Unexpected error processing SQL: {e}')
            raise ValueError(f'Failed to process SQL query: {str(e)}')
