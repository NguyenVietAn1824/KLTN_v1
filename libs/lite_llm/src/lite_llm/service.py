from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from collections.abc import Generator
from contextlib import asynccontextmanager
from contextlib import contextmanager
from typing import Any
from typing import Dict
from typing import Optional

import httpx
from base import BaseModel
from base import BaseService
from logger import get_logger

from .datatypes import CompletionMessage
from .datatypes import Message
from .datatypes import Response
from .datatypes import TokensLLM
from .datatypes import TypeMessage
from .settings import LiteLLMSetting

logger = get_logger(__name__)


class LiteLLMInput(BaseModel):
    """
    Input model for LiteLLM service requests.

    Attributes:
        message (Message): The message(s) to send to the LLM.
        return_type (type[BaseModel] | None): Expected response type for structured output.
        frequency_penalty (Optional[int]): Frequency penalty for token repetition.
        n (Optional[int]): Number of completions to generate.
        model (Optional[str]): The model name to use for inference.
        presence_penalty (Optional[int]): Presence penalty for token usage.
        max_completion_tokens (Optional[int]): Maximum number of tokens in completion.
        tools (Optional[list[dict[str, str | object]]]): Tools available to the model.
        count_tokens (bool): Whether to count tokens in the response.
        stream (bool): Whether to stream the response.
    """

    message: Message
    return_type: type[BaseModel] | None = None
    frequency_penalty: Optional[int] = None
    n: Optional[int] = None
    model: Optional[str] = None
    presence_penalty: Optional[int] = None
    tools: Optional[list[dict[str, str | object]]] = None
    count_tokens: bool = False
    stream: bool = False


class LiteLLMOutput(BaseModel):
    """
    Output model for LiteLLM service responses.

    Attributes:
        response (Response): The response content from the LLM.
        metadata (dict[str, Any]): Additional metadata about the response.
        count_tokens (bool): Whether tokens were counted in this response.
        tokens (TokensLLM): Token usage information for the request/response.
    """

    response: Response
    metadata: dict[str, Any] = {}
    count_tokens: bool = False
    tokens: TokensLLM = TokensLLM()


class LiteLLMEmbeddingInput(BaseModel):
    """
    Input model for LiteLLM embedding requests.

    Attributes:
        input (str | list[str]): The text(s) to embed.
        embedding_model (str): The model name to use for embedding.
        encoding_format (Optional[str]): The format to return the embeddings in.
        count_tokens (bool): Whether to count tokens in the response.
    """

    input: str | list[str]
    embedding_model: str
    encoding_format: Optional[str] = None
    dimensions: int
    count_tokens: bool = False


class LiteLLMEmbeddingOutput(BaseModel):
    """
    Output model for LiteLLM embedding responses.

    Attributes:
        vector (list): The embedding vector returned from the API.
    """

    vector: list


class LiteLLMService(BaseService):
    """
    Service for interacting with LiteLLM API for language model inference and embedding generation.

    This service provides both synchronous and asynchronous methods for making
    requests to LiteLLM-compatible APIs, with support for various models including
    OpenAI and Claude models. It supports both text completion and embedding operations.

    Attributes:
        settings (LiteLLMSetting): Configuration settings for the service.
    """

    settings: LiteLLMSetting

    @property
    def headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self.settings.token.get_secret_value()}',
        }

    @property
    @contextmanager
    def client(self) -> Generator[httpx.Client]:
        """
        Context manager for creating a synchronous HTTP client.

        Yields:
            httpx.Client: A configured HTTP client with authentication headers.

        Raises:
            ValueError: If authentication fails (401 status).
            httpx.HTTPStatusError: For other HTTP errors.
        """
        client = httpx.Client(
            base_url=self.settings.url.unicode_string().rstrip('/'),
            headers={
                'Authorization': f'Bearer {self.settings.token.get_secret_value()}',
                'Content-Type': 'application/json',
            },
            timeout=httpx.Timeout(self.settings.timeout, connect=self.settings.connect_timeout),
        )
        try:
            yield client
        except Exception as e:
            raise e
        finally:
            client.close()

    @property
    @asynccontextmanager
    async def async_client(self) -> AsyncGenerator[httpx.AsyncClient]:
        """
        Async context manager for creating an asynchronous HTTP client.

        Yields:
            httpx.AsyncClient: A configured async HTTP client with authentication headers.
        """
        client = httpx.AsyncClient(
            base_url=self.settings.url.unicode_string().rstrip('/'),
            headers={
                'Authorization': f'Bearer {self.settings.token.get_secret_value()}',
                'Content-Type': 'application/json',
            },
            timeout=httpx.Timeout(self.settings.timeout, connect=self.settings.connect_timeout),
            limits=httpx.Limits(max_connections=self.settings.max_connections, max_keepalive_connections=self.settings.max_keepalive_connections),
        )
        try:
            yield client
        finally:
            await client.aclose()

    def process(self, inputs: LiteLLMInput) -> LiteLLMOutput:
        """
        Process a synchronous LLM request.

        Args:
            inputs (LiteLLMInput): Input parameters for the LLM request.

        Returns:
            LiteLLMOutput: The processed output from the LLM.
        """
        return self.__inference_by_llm(
            message=inputs.message,
            return_type=inputs.return_type,
            frequency_penalty=(
                inputs.frequency_penalty if inputs.frequency_penalty else 0
            ),
            n=inputs.n if inputs.n else 1,
            model=inputs.model if inputs.model else self.settings.model,
            presence_penalty=inputs.presence_penalty if inputs.presence_penalty else 0,
            count_tokens=inputs.count_tokens,
        )

    async def process_async(self, inputs: LiteLLMInput) -> LiteLLMOutput:
        """
        Process an asynchronous LLM request.

        Args:
            inputs (LiteLLMInput): Input parameters for the LLM request.

        Returns:
            LiteLLMOutput: The processed output from the LLM.
        """
        return await self.__inference_by_llm_async(
            message=inputs.message,
            return_type=inputs.return_type,
            frequency_penalty=(
                inputs.frequency_penalty if inputs.frequency_penalty else 0
            ),
            n=inputs.n if inputs.n else 1,
            model=inputs.model if inputs.model else self.settings.model,
            presence_penalty=inputs.presence_penalty if inputs.presence_penalty else 0,
            count_tokens=inputs.count_tokens,
        )

    def embedding(self, inputs: LiteLLMEmbeddingInput) -> LiteLLMEmbeddingOutput:
        """
        Generate embeddings for the given input text(s).

        Args:
            inputs (LiteLLMEmbeddingInput): Input parameters for the embedding request.

        Returns:
            LiteLLMEmbeddingOutput: The processed embedding output.
        """

        if len(inputs.input) > self.settings.max_length:
            logger.warning(
                'Input too long for embedding generation, truncating to max length',
                extra={'input': inputs.input, 'input_length': len(inputs.input)},
            )
            inputs.input = inputs.input[: self.settings.max_length]

        return self.__embedding_by_llm(
            input=inputs.input,
            embedding_model=inputs.embedding_model,
            encoding_format=inputs.encoding_format,
            count_tokens=inputs.count_tokens,
            dimensions=inputs.dimensions,
        )

    async def embedding_async(
        self,
        inputs: LiteLLMEmbeddingInput,
    ) -> LiteLLMEmbeddingOutput:
        """
        Generate embeddings for the given input text(s) asynchronously.

        Args:
            inputs (LiteLLMEmbeddingInput): Input parameters for the embedding request.

        Returns:
            LiteLLMEmbeddingOutput: The processed embedding output.
        """

        if len(inputs.input) > self.settings.max_length:
            logger.warning(
                'Input too long for embedding generation, truncating to max length',
                extra={'input': inputs.input, 'input_length': len(inputs.input)},
            )

            inputs.input = inputs.input[: self.settings.max_length]

        return await self.__embedding_by_llm_async(
            input=inputs.input,
            embedding_model=inputs.embedding_model,
            encoding_format=inputs.encoding_format,
            count_tokens=inputs.count_tokens,
            dimensions=inputs.dimensions,
        )

    async def process_stream_async(
        self,
        inputs: LiteLLMInput,
    ) -> AsyncGenerator[str, None]:
        """
        Process an asynchronous streaming LLM request.

        Args:
            inputs (LiteLLMInput): Input parameters for the LLM request.

        Yields:
            str: Chunks of the response text as they arrive.
        """
        async with self.async_client as client:
            payload = self.__build_request_payload(
                message=inputs.message,
                return_type=inputs.return_type,
                frequency_penalty=(
                    inputs.frequency_penalty if inputs.frequency_penalty else 0
                ),
                n=inputs.n if inputs.n else 1,
                model=inputs.model if inputs.model else self.settings.model,
                presence_penalty=inputs.presence_penalty if inputs.presence_penalty else 0,
            )
            payload['stream'] = True

            async with client.stream(
                'POST',
                '/chat/completions',
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            if chunk.get('choices') and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta and delta['content']:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue

    def __inference_by_llm(
        self,
        *,
        message: Message,
        return_type: type[BaseModel] | None,
        frequency_penalty: int,
        n: int,
        model: str,
        presence_penalty: int,
        count_tokens: bool = False,
    ) -> LiteLLMOutput:
        """
        Execute synchronous inference using the LLM API.

        Args:
            message (Message): The message(s) to send to the LLM.
            return_type (type[BaseModel] | None): Expected response type for structured output.
            frequency_penalty (int): Frequency penalty for token repetition.
            n (int): Number of completions to generate.
            model (str): The model name to use for inference.
            presence_penalty (int): Presence penalty for token usage.
            count_tokens (bool): Whether to count tokens in the response.

        Returns:
            LiteLLMOutput: The processed response from the LLM.

        Raises:
            httpx.HTTPStatusError: For HTTP-related errors.
            Exception: For other unexpected errors.
        """
        with self.client as client:
            payload = self.__build_request_payload(
                message=message,
                return_type=return_type,
                frequency_penalty=frequency_penalty,
                n=n,
                model=model,
                presence_penalty=presence_penalty,
            )

            try:
                response = client.post('/v1/chat/completions', json=payload)
                response.raise_for_status()
                response_data = response.json()

                return self.__postprocessing_response(
                    response=response_data,
                    count_token=count_tokens,
                    return_type=return_type,
                )

            except Exception as e:
                raise e

    async def __inference_by_llm_async(
        self,
        *,
        message: Message,
        return_type: type[BaseModel] | None,
        frequency_penalty: int,
        n: int,
        model: str,
        presence_penalty: int,
        count_tokens: bool = False,
    ) -> LiteLLMOutput:
        """
        Execute asynchronous inference using the LLM API.

        Args:
            message (Message): The message(s) to send to the LLM.
            return_type (type[BaseModel] | None): Expected response type for structured output.
            frequency_penalty (int): Frequency penalty for token repetition.
            n (int): Number of completions to generate.
            model (str): The model name to use for inference.
            presence_penalty (int): Presence penalty for token usage.
            count_tokens (bool): Whether to count tokens in the response.

        Returns:
            LiteLLMOutput: The processed response from the LLM.

        Raises:
            httpx.HTTPStatusError: For HTTP-related errors.
            Exception: For other unexpected errors.
        """
        async with self.async_client as client:
            payload = self.__build_request_payload(
                message=message,
                return_type=return_type,
                frequency_penalty=frequency_penalty,
                n=n,
                model=model,
                presence_penalty=presence_penalty,
            )
            try:
                response = await client.post('/v1/chat/completions', json=payload)
                response.raise_for_status()
                response_data = response.json()

                return self.__postprocessing_response(
                    response=response_data,
                    count_token=count_tokens,
                    return_type=return_type,
                )

            except Exception as e:
                raise e

    def __embedding_by_llm(
        self,
        *,
        input: str | list[str],
        embedding_model: str,
        encoding_format: str | None,
        count_tokens: bool = False,
        dimensions: int,
    ) -> LiteLLMEmbeddingOutput:
        """
        Execute synchronous embedding generation using the LLM API.

        Args:
            input (str | list[str]): The text(s) to embed.
            embedding_model (str): The model name to use for embedding.
            encoding_format (str | None): The format to return the embeddings in.
            count_tokens (bool): Whether to count tokens in the response.

        Returns:
            LiteLLMEmbeddingOutput: The processed embedding response.

        Raises:
            httpx.HTTPStatusError: For HTTP-related errors.
            Exception: For other unexpected errors.
        """
        with self.client as client:
            payload = self.__build_embedding_payload(
                input=input,
                embedding_model=embedding_model,
                encoding_format=encoding_format,
                dimensions=dimensions,
            )
            try:
                response = client.post('/v1/embeddings', json=payload)
                response.raise_for_status()
                response_data = response.json()

                return self.__postprocessing_embedding_response(
                    response=response_data,
                    count_token=count_tokens,
                )

            except Exception as e:
                raise e

    async def __embedding_by_llm_async(
        self,
        *,
        input: str | list[str],
        embedding_model: str,
        encoding_format: str | None,
        count_tokens: bool = False,
        dimensions: int,
    ) -> LiteLLMEmbeddingOutput:
        """
        Execute asynchronous embedding generation using the LLM API.

        Args:
            input (str | list[str]): The text(s) to embed.
            embedding_model (str): The model name to use for embedding.
            encoding_format (str | None): The format to return the embeddings in.
            count_tokens (bool): Whether to count tokens in the response.

        Returns:
            LiteLLMEmbeddingOutput: The processed embedding response.

        Raises:
            httpx.HTTPStatusError: For HTTP-related errors.
            Exception: For other unexpected errors.
        """
        async with self.async_client as client:
            payload = self.__build_embedding_payload(
                input=input,
                embedding_model=embedding_model,
                encoding_format=encoding_format,
                dimensions=dimensions,
            )

            try:
                response = await client.post('/v1/embeddings', json=payload)
                response.raise_for_status()
                response_data = response.json()

                return self.__postprocessing_embedding_response(
                    response=response_data,
                    count_token=count_tokens,
                )

            except Exception as e:
                raise e

    def __build_request_payload(
        self,
        message: Message,
        return_type: type[BaseModel] | None,
        frequency_penalty: int,
        n: int,
        model: str,
        presence_penalty: int,
    ) -> Dict[str, Any]:
        """
        Build the request payload for the chat completion API.

        Args:
            message (Message): The message(s) to include in the request.
            return_type (type[BaseModel] | None): Expected response type for structured output.
            frequency_penalty (int): Frequency penalty for token repetition.
            n (int): Number of completions to generate.
            model (str): The model name to use for inference.
            presence_penalty (int): Presence penalty for token usage.

        Returns:
            Dict[str, Any]: The formatted request payload for the API.
        """
        if 'claude' in model.lower():
            payload = {
                'model': model,
                'messages': [self.__parse_to_openai_message(m) for m in message],
                'max_tokens': self.settings.max_completion_tokens,
                'n': n,
            }
        else:
            payload = {
                'model': model,
                'messages': [self.__parse_to_openai_message(m) for m in message],
                'max_tokens': self.settings.max_completion_tokens,
                'frequency_penalty': frequency_penalty,
                'presence_penalty': presence_penalty,
                'n': n,
                'temperature': self.settings.temperature,
            }

        if return_type:
            payload['response_format'] = {
                'type': 'json_schema',
                'json_schema': {
                    'name': return_type.__name__,
                    'schema': {
                        **return_type.model_json_schema(),
                        'additionalProperties': False,
                    },
                    'strict': True,
                },
            }
        return payload

    def __parse_to_openai_message(self, message: CompletionMessage) -> Dict[str, Any]:
        """
        Parse CompletionMessage to OpenAI API message format.

        Args:
            message (CompletionMessage): CompletionMessage object to convert.

        Returns:
            Dict[str, str]: OpenAI API message format with role and content fields.
        """
        if message.type == TypeMessage.IMAGE_URL and message.image_url:
            return {
                'role': message.role.value,
                'content': [{
                    'type': message.type.value,
                    'image_url': message.image_url,
                }],
            }
        return {
            'role': message.role.value,
            'content': message.content,
        }

    def __postprocessing_response(
        self,
        response: Dict[str, Any],
        count_token: bool,
        return_type: type[BaseModel] | None,
    ) -> LiteLLMOutput:
        """
        Post-process the response from chat completion API.

        Args:
            response (Dict[str, Any]): The response object received from the LLM API.
            count_token (bool): Flag indicating whether to count tokens used in the response.
            return_type (type[BaseModel] | None): The expected return type for the response. If provided, the response will be validated against this type.

        Returns:
            LiteLLMOutput: The processed output containing the response content, token count, and any tokens used in the completion.

        Raises:
            ValueError: If the response content is empty.
        """
        if not response.get('choices') or not response['choices']:
            raise ValueError('No choices returned in response')

        choice = response['choices'][0]
        content = choice.get('message', {}).get('content')

        if not content:
            raise ValueError('Response returned by client is empty')

        tokens = TokensLLM()
        if count_token and response.get('usage'):
            usage = response['usage']
            tokens.completion_tokens = usage.get('completion_tokens', 0)
            tokens.prompt_tokens = usage.get('prompt_tokens', 0)
            tokens.total_tokens = usage.get('total_tokens', 0)

        return LiteLLMOutput(
            response=(
                content
                if not return_type
                else return_type.model_validate_json(
                    content,
                )
            ),
            count_tokens=count_token,
            tokens=tokens,
        )

    def __build_embedding_payload(
        self,
        input: str | list[str],
        embedding_model: str,
        encoding_format: str | None,
        dimensions: int,
    ) -> Dict[str, Any]:
        """
        Build the request payload for the embedding API.

        Args:
            input (str | list[str]): The text(s) to embed.
            embedding_model (str): The model name to use for embedding.
            encoding_format (str | None): The format to return the embeddings in.

        Returns:
            Dict[str, Any]: The formatted request payload for the API.
        """
        payload = {
            'input': input,
            'model': embedding_model,
            'dimensions': dimensions,
        }

        if encoding_format:
            payload['encoding_format'] = encoding_format

        return payload

    def __postprocessing_embedding_response(
        self,
        response: Dict[str, Any],
        count_token: bool,
    ) -> LiteLLMEmbeddingOutput:
        """
        Post-process the response from embedding API.

        Args:
            response (Dict[str, Any]): The response object received from the embedding API.
            count_token (bool): Flag indicating whether to count tokens used in the response (currently unused).

        Returns:
            LiteLLMEmbeddingOutput: The processed output containing the first embedding vector.

        Raises:
            ValueError: If the response data is empty or invalid.
        """
        if not response.get('data'):
            raise ValueError('No data returned in embedding response')

        embeddings = [item['embedding'] for item in response['data']]

        tokens = TokensLLM()
        if count_token and response.get('usage'):
            usage = response['usage']
            tokens.prompt_tokens = usage.get('prompt_tokens', 0)
            tokens.total_tokens = usage.get('total_tokens', 0)

        return LiteLLMEmbeddingOutput(
            vector=embeddings[0],
        )

    async def check_health(self) -> bool:
        """Check if the LiteLLM service is healthy

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.settings.timeout, connect=self.settings.connect_timeout),
                limits=httpx.Limits(max_connections=self.settings.max_connections, max_keepalive_connections=self.settings.max_keepalive_connections),
            ) as client:
                r = await client.get(
                    self.settings.url.unicode_string().rstrip('/') + '/health',
                    headers=self.headers,
                )
            if r.status_code == 200 and r.json()['unhealthy_count'] == 0:
                return True

            logger.warning(
                'LiteLLM Service are unhealthy',
                extra={
                    'unhealthy_count': r.json()['unhealthy_count'],
                    'healthy_count': r.json()['healthy_count'],
                },
            )
            return False
        except Exception as e:
            raise e
