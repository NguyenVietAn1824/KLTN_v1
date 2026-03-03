from __future__ import annotations

import unicodedata

import sqlglot
from base import BaseService
from aqi_agent.shared.settings import AutocorrectorSettings
from logger import get_logger
from rapidfuzz import fuzz
from rapidfuzz import process
from redis import Redis  # type: ignore[import-untyped]
from sqlglot import exp
from sqlglot.errors import ParseError

from .models import AutocorrectorInput
from .models import AutocorrectorOutput

logger = get_logger(__name__)


class FuzzyCorrectorService(BaseService):
    """Service for fuzzy correction of SQL WHERE clause values using Redis cache."""

    redis_client: Redis
    settings: AutocorrectorSettings

    def _remove_accents(self, input_str: str) -> str:
        try:
            nfkd_form = unicodedata.normalize('NFKD', input_str)
            return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])
        except Exception:
            logger.warning(
                'Failed to remove accents from input string, using original string.',
                extra={'input_str': input_str},
            )
            return input_str

    def _extract_table_mapping(self, expression: exp.Expression) -> dict[str, str]:
        try:
            mapping: dict[str, str] = {}
            for table in expression.find_all(exp.Table):
                real_name = table.name
                alias = table.alias or real_name
                if real_name:
                    mapping[alias] = real_name
                    if real_name not in mapping:
                        mapping[real_name] = real_name
            return mapping
        except Exception:
            logger.exception(
                'Failed to extract table mapping from SQL expression.',
                extra={'expression': expression.sql() if expression else None},
            )
            raise

    def _get_column_name(self, column: exp.Column, table_mapping: dict[str, str]) -> str:
        try:
            table_alias = column.table
            column_name = column.name

            real_table_name = None
            if table_alias:
                real_table_name = table_mapping.get(table_alias, table_alias)
            elif table_mapping:
                real_table_name = list(table_mapping.values())[0]

            if real_table_name and column_name:
                return f'{real_table_name}.{column_name}'

            return column_name or ''
        except Exception:
            logger.exception(
                'Failed to get column name from SQL expression.',
                extra={'column': column.sql() if column else None},
            )
            raise

    def _find_cached_values_for_column(self, column_name: str) -> dict[str, list[str]]:
        try:
            pattern = f'{self.settings.redis_key_prefix}:{column_name}'
            matched_keys = []

            for key in self.redis_client.scan_iter(match=pattern, count=100):
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                matched_keys.append(key)

            result = {}
            for key in matched_keys:
                values = self.redis_client.lrange(key, 0, -1)
                decoded_values = [
                    v.decode('utf-8') if isinstance(v, bytes) else v
                    for v in values
                ]
                if decoded_values:
                    result[key] = decoded_values

            return result
        except Exception:
            logger.exception(
                'Failed to find cached values for column.',
                extra={'column_name': column_name},
            )
            raise

    def _fuzzy_match(
        self,
        query_value: str,
        cached_values: list[str],
        threshold: int,
        max_matches: int | None,
    ) -> list[str]:
        try:
            if not query_value or not cached_values:
                return []

            query_normalized = self._remove_accents(query_value.lower().strip())

            normalized_cache_map = {}
            for val in cached_values:
                norm_val = self._remove_accents(val.lower().strip())
                if norm_val not in normalized_cache_map:
                    normalized_cache_map[norm_val] = val

            normalized_cached_list = list(normalized_cache_map.keys())

            results = process.extract(
                query_normalized,
                normalized_cached_list,
                scorer=fuzz.WRatio if len(query_normalized) > 5 else fuzz.QRatio,
                limit=max_matches,
                score_cutoff=threshold,
            )

            final_matches = []
            for match_str, _, _ in results:
                original_val = normalized_cache_map[match_str]
                final_matches.append(original_val)

            return final_matches
        except Exception:
            logger.exception(
                'Failed to perform fuzzy match.',
                extra={'query_value': query_value, 'cached_values': cached_values},
            )
            raise

    def _extract_where_equality_conditions(
        self, expression: exp.Expression,
    ) -> list[dict]:
        try:
            conditions: list[dict] = []

            where = expression.find(exp.Where)
            if not where:
                return conditions

            for eq_node in where.find_all(exp.EQ):
                left = eq_node.left
                right = eq_node.right

                if not isinstance(left, exp.Column):
                    continue
                if not isinstance(right, exp.Literal) or not right.is_string:
                    continue

                conditions.append({
                    'column': left,
                    'value': right.this,
                    'eq_node': eq_node,
                })

            return conditions
        except Exception:
            logger.exception(
                'Failed to extract WHERE equality conditions from SQL expression.',
                extra={'expression': expression.sql() if expression else None},
            )
            raise

    def process(self, input: AutocorrectorInput) -> AutocorrectorOutput:
        try:
            sql_query = input.sql_query
            fuzzy_threshold = self.settings.fuzzy_threshold
            max_matches = self.settings.max_fuzzy_matches

            if not sql_query or not sql_query.strip():
                return AutocorrectorOutput(corrected_sql_query=sql_query)

            try:
                parsed_statements = sqlglot.parse(sql_query)
            except ParseError:
                return AutocorrectorOutput(corrected_sql_query=sql_query)

            if not parsed_statements:
                return AutocorrectorOutput(corrected_sql_query=sql_query)

            for expression in parsed_statements:
                if expression is None:
                    continue

                table_mapping = self._extract_table_mapping(expression)
                conditions = self._extract_where_equality_conditions(expression)

                for cond in conditions:
                    column: exp.Column = cond['column']
                    original_value: str = cond['value']
                    eq_node: exp.EQ = cond['eq_node']

                    column_str = self._get_column_name(column, table_mapping)
                    cached_map = self._find_cached_values_for_column(column_str)

                    if not cached_map:
                        continue

                    all_cached_values = [v for values in cached_map.values() for v in values]

                    seen = set()
                    unique_cached = []
                    for v in all_cached_values:
                        if v not in seen:
                            seen.add(v)
                            unique_cached.append(v)

                    if original_value in unique_cached:
                        continue

                    matches = self._fuzzy_match(
                        original_value, unique_cached, fuzzy_threshold, max_matches,
                    )

                    if not matches:
                        continue

                    if len(matches) == 1:
                        new_node = exp.EQ(
                            this=column.copy(),
                            expression=exp.Literal.string(matches[0]),
                        )
                    else:
                        new_node = exp.In(
                            this=column.copy(),
                            expressions=[exp.Literal.string(m) for m in matches],
                        )

                    eq_node.replace(new_node)

            corrected_sql = '; '.join(
                expr.sql() for expr in parsed_statements if expr is not None
            )

            return AutocorrectorOutput(corrected_sql_query=corrected_sql)
        except Exception:
            logger.exception(
                'Failed to process SQL query for fuzzy correction.',
                extra={'sql_query': input.sql_query},
            )
            raise
