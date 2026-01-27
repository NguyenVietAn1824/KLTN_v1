from __future__ import annotations

"""Hasura GraphQL service for executing queries and introspection.

This module provides the infrastructure layer for interacting with Hasura GraphQL Engine,
following the sun_assistant pattern. It handles query execution, schema introspection,
and error handling.
"""

import asyncio
from typing import Any

import httpx
from base import BaseModel


class HasuraSettings(BaseModel):
    """Settings for Hasura GraphQL connection.

    Attributes:
        endpoint (str): Hasura GraphQL endpoint URL
        admin_secret (str): Admin secret for authentication
        timeout (int): Request timeout in seconds (default: 30)
    """

    endpoint: str
    admin_secret: str
    timeout: int = 30


class HasuraService(BaseModel):
    """Service for executing GraphQL queries against Hasura.

    This service provides methods for:
    - Executing GraphQL queries and mutations
    - Schema introspection
    - Table and field metadata retrieval
    - Error handling and retry logic

    Follows the sun_assistant HasuraService pattern with async/await.

    Attributes:
        settings (HasuraSettings): Hasura connection configuration
    """

    settings: HasuraSettings

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for Hasura requests.

        Returns:
            Dictionary containing Content-Type and admin secret headers

        Example:
            >>> headers = service._get_headers()
            >>> print(headers['x-hasura-admin-secret'])
        """
        return {
            'Content-Type': 'application/json',
            'x-hasura-admin-secret': self.settings.admin_secret,
        }

    async def execute_query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query against Hasura.

        Args:
            query (str): GraphQL query string
            variables (dict | None): Query variables (optional)

        Returns:
            dict: Query response containing 'data' and potentially 'errors'

        Raises:
            httpx.HTTPError: If HTTP request fails
            Exception: If response contains GraphQL errors

        Example:
            >>> query = '''
            ... query GetDistrict($id: String!) {
            ...   districts(where: {id: {_eq: $id}}) {
            ...     id
            ...     name
            ...   }
            ... }
            ... '''
            >>> result = await service.execute_query(query, {"id": "001"})
            >>> print(result['data']['districts'])
        """
        payload = {
            'query': query,
        }
        if variables:
            payload['variables'] = variables

        async with httpx.AsyncClient(timeout=self.settings.timeout) as client:
            response = await client.post(
                self.settings.endpoint,
                json=payload,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            result = response.json()

            # Check for GraphQL errors
            if 'errors' in result:
                error_messages = [err.get('message', str(err)) for err in result['errors']]
                raise Exception(f"GraphQL errors: {', '.join(error_messages)}")

            return result

    async def introspect_schema(self) -> dict[str, Any]:
        """Introspect Hasura schema to get all types and fields.

        Uses GraphQL introspection query to retrieve complete schema information
        including tables, fields, relationships, and types.

        Returns:
            dict: Schema introspection result containing __schema data

        Raises:
            Exception: If introspection query fails

        Example:
            >>> schema = await service.introspect_schema()
            >>> tables = [t['name'] for t in schema['data']['__schema']['types']]
            >>> print(f"Available tables: {tables}")
        """
        introspection_query = """
        query IntrospectionQuery {
          __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
              ...FullType
            }
          }
        }
        
        fragment FullType on __Type {
          kind
          name
          description
          fields(includeDeprecated: true) {
            name
            description
            args {
              ...InputValue
            }
            type {
              ...TypeRef
            }
          }
          inputFields {
            ...InputValue
          }
          interfaces {
            ...TypeRef
          }
          enumValues(includeDeprecated: true) {
            name
            description
          }
          possibleTypes {
            ...TypeRef
          }
        }
        
        fragment InputValue on __InputValue {
          name
          description
          type { ...TypeRef }
          defaultValue
        }
        
        fragment TypeRef on __Type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        return await self.execute_query(introspection_query)

    async def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """Get schema information for a specific table.

        Retrieves field names, types, and descriptions for the specified table
        by querying the Hasura introspection API.

        Args:
            table_name (str): Name of the table to introspect (e.g., 'districts')

        Returns:
            dict: Table schema containing fields and their types

        Raises:
            Exception: If table not found or query fails

        Example:
            >>> schema = await service.get_table_schema('districts')
            >>> fields = [f['name'] for f in schema['fields']]
            >>> print(f"District fields: {fields}")
        """
        query = f"""
        query {{
          __type(name: "{table_name}") {{
            name
            description
            fields {{
              name
              description
              type {{
                name
                kind
                ofType {{
                  name
                  kind
                }}
              }}
            }}
          }}
        }}
        """

        result = await self.execute_query(query)
        table_type = result.get('data', {}).get('__type')

        if not table_type:
            raise Exception(f"Table '{table_name}' not found in Hasura schema")

        return table_type

    async def get_available_tables(self) -> list[str]:
        """Get list of all available tables in Hasura.

        Filters the schema to return only user-defined tables (excluding
        system tables and introspection types).

        Returns:
            list[str]: List of table names available in Hasura

        Example:
            >>> tables = await service.get_available_tables()
            >>> print(f"Available tables: {tables}")
            ['districts', 'distric_stats', 'provinces', 'air_component']
        """
        schema = await self.introspect_schema()
        types = schema.get('data', {}).get('__schema', {}).get('types', [])

        # Filter to get only user tables (exclude system types)
        tables = [
            t['name']
            for t in types
            if t.get('kind') == 'OBJECT'
            and not t['name'].startswith('__')
            and not t['name'].startswith('_')
            and t.get('fields')  # Has fields (is a table)
        ]

        return tables

    async def validate_tables_exist(self, table_names: list[str]) -> dict[str, bool]:
        """Validate that specified tables exist in Hasura schema.

        Args:
            table_names (list[str]): List of table names to validate

        Returns:
            dict[str, bool]: Mapping of table names to existence status

        Example:
            >>> result = await service.validate_tables_exist(['districts', 'fake_table'])
            >>> print(result)
            {'districts': True, 'fake_table': False}
        """
        available_tables = await self.get_available_tables()
        return {table: table in available_tables for table in table_names}

    async def test_connection(self) -> bool:
        """Test Hasura connection with a simple query.

        Returns:
            bool: True if connection successful, False otherwise

        Example:
            >>> is_connected = await service.test_connection()
            >>> print(f"Hasura connected: {is_connected}")
        """
        try:
            query = """
            query {
              __schema {
                queryType {
                  name
                }
              }
            }
            """
            result = await self.execute_query(query)
            return 'data' in result
        except Exception:
            return False
