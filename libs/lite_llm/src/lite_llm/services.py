from __future__ import annotations

from typing import Any 
from typing import Optional
import httpx
from base import BaseService 
from base import BaseModel
from logger import get_logger
from functools import cached_property

from .settings import LiteLLMSetting
from .models import LiteLLMInput
from .models import LiteLLMOutput
from .models import Messages
from .models import LiteLLMEmbeddingInput
from .models import LiteLLMEmbeddingOutput


logger = get_logger(__name__)

class LiteLLMService(BaseService):
    litellm_setting: LiteLLMSetting 
    async_client: Optional[httpx.AsyncClient] = None
    client: Optional[httpx.Client] = None
    
    @cached_property
    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.litellm_setting.token.get_secret_value()}",
        }
    
    @property
    def _async_client(self) -> httpx.AsyncClient:
        if not self.async_client or self.async_client.is_closed:
            self.async_client = httpx.AsyncClient(
                timeout=httpx.Timeout(100.0, connect=15.0),
                limits=httpx.Limits(max_connections=200, max_keepalive_connections=40),
            )
        return self.async_client
    
    @property
    def _client(self) -> httpx.Client:
        if not self.client or self.client.is_closed:
            self.client = httpx.Client(
                timeout=httpx.Timeout(100.0, connect=15.0),
                limits=httpx.Limits(max_connections=200, max_keepalive_connections=40),
            )
        return self.client
    
    def embedding_llm(
        self, 
        model: str,
        inputs: str,
    ) -> LiteLLMEmbeddingOutput:
        """ Process the input and return the output.

        Args:
            model (str): The model to use for processing.
            inputs (str): The inputs to process.

        Returns:
            LiteLLMEmbeddingOutput: The processed output.
        """
        
        payload = {
            "model": model,
            "input": inputs,
            "output_dimensionality": self.litellm_setting.dimension,
        }
        
        try:
            response = self._client.post(
                url=str(self.litellm_setting.url) + "v1/embeddings",
                headers=self.headers,
                json=payload,
            )
            
            if response.status_code == 200:
                return LiteLLMEmbeddingOutput(
                    embedding=response.json()['data'][0]['embedding'],
                )
            else:
                logger.error(
                    "Request failed with status code",
                    extra={
                        "status_code": response.status_code,
                        "model": model,
                        "inputs": inputs,
                    }
                )
                return LiteLLMEmbeddingOutput(
                    embedding=[],
                )
        except httpx.RequestError as e:
            logger.exception(
                "An error occurred while processing the request",
                extra={
                    "error": str(e),
                    "inputs": inputs,
                    "model": model,
                }
            )
            return LiteLLMEmbeddingOutput(
                embedding=[],
            )
            
    async def embedding_llm_async(
        self, 
        model: str,
        inputs: str,
    ) -> LiteLLMEmbeddingOutput:
        """Asynchronously process the input and return the output.

        Args:
            model (str): The model to use for processing.
            inputs (str): The inputs to process.

        Returns:
            LiteLLMEmbeddingOutput: The processed output.
        """
        
        payload = {
            "model": model,
            "input": inputs,
            "output_dimensionality": self.litellm_setting.dimension,
        }
        
        try:
            response = await self._async_client.post(
                url=str(self.litellm_setting.url) + "v1/embeddings",
                headers=self.headers,
                json=payload,
            )
            
            if response.status_code == 200:
                return LiteLLMEmbeddingOutput(
                    embedding=response.json()['data'][0]['embedding'],
                )
            else:
                logger.error(
                    "Request failed with status code",
                    extra={
                        "status_code": response.status_code,
                        "model": model,
                        "inputs": inputs,
                    }
                )
                return LiteLLMEmbeddingOutput(
                    embedding=[],
                )
        except httpx.RequestError as e:
            logger.exception(
                "An error occurred while processing the request",
                extra={
                    "error": str(e),
                    "inputs": inputs,
                    "model": model,
                }
            )
            return LiteLLMEmbeddingOutput(
                embedding=[],
            )
    
    def _inference_llm(
        self, 
        messages: Messages,
        model: str,
        response_format: type[BaseModel] | None,
        temperature: float,
        top_p: float,
        n: int,
        frequency_penalty: float,
        max_completion_tokens: int,
        reasoning_effort: str,
    ) -> LiteLLMOutput:
        """ Process the input and return the output.

        Args:
            messages (Messages): The messages to process.
            model (str): The model to use for processing.
            response_format (type[BaseModel] | None): The response format.
            temperature (float): The temperature for the model.
            top_p (float): The top_p value for the model.
            n (int): The number of responses to generate.
            frequency_penalty (float): The frequency penalty for the model.
            max_completion_tokens (int): The maximum number of completion tokens.
            reasoning_effort (str): The reasoning effort level.
            
        Returns:
            LiteLLMOutput: The processed output.
        """

        payload = self._build_payload(
            messages=messages,
            model=model,
            response_format=response_format,
            frequency_penalty=frequency_penalty,
            n=n,
            temperature=temperature,
            top_p=top_p,
            max_completion_tokens=max_completion_tokens,
            reasoning_effort=reasoning_effort,
        )

        try:
            response = self._client.post(
                url=str(self.litellm_setting.url) + "/chat/completions",
                headers=self.headers,
                json=payload,
            )
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                return LiteLLMOutput(
                    response=content if not response_format else response_format.model_validate_json(content),
                    completion_tokens=response.json()['usage']['completion_tokens'],
                )
            else:
                logger.error(f"Request failed with status code {response.status_code}: {response.text}")
                return LiteLLMOutput(
                    response="",
                    completion_tokens=0,
                )
        except httpx.RequestError as e:
            logger.exception(
                "An error occurred while processing the request",
                extra={
                    "error": str(e),
                }
            )
            return LiteLLMOutput(
                response="",
                completion_tokens=0,
            )
            
    async def _inference_llm_async(
        self, 
        messages: Messages,
        model: str,
        response_format: type[BaseModel] | None,
        temperature: float,
        top_p: float,
        n: int,
        frequency_penalty: float,
        max_completion_tokens: int,
        reasoning_effort: str | None = None,
    ) -> LiteLLMOutput:
        """Asynchronously process the input and return the output.

        Args:
            messages (Messages): The messages to process.
            model (str): The model to use for processing.
            response_format (type[BaseModel] | None): The response format.
            temperature (float): The temperature for the model.
            top_p (float): The top_p value for the model.
            n (int): The number of responses to generate.
            frequency_penalty (float): The frequency penalty for the model.
            max_completion_tokens (int): The maximum number of completion tokens.
            reasoning_effort (str): The reasoning effort level.
        
        Returns:
            LiteLLMOutput: The processed output.
        """

        payload = self._build_payload(
            messages=messages,
            model=model,
            response_format=response_format,
            frequency_penalty=frequency_penalty,
            n=n,
            temperature=temperature,
            top_p=top_p,
            max_completion_tokens=max_completion_tokens,
            reasoning_effort=reasoning_effort,
        )
        
        try:
            response = await self._async_client.post(
                url=str(self.litellm_setting.url) + "/chat/completions",
                headers=self.headers,
                json=payload,
            )
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                return LiteLLMOutput(
                    response=content if not response_format else response_format.model_validate_json(content),
                    completion_tokens=response.json()['usage']['completion_tokens'],
                )
            else:
                logger.error(f"Request failed with status code {response.status_code}: {response.text}")
                return LiteLLMOutput(
                    response="",
                    completion_tokens=0,
                )
        except httpx.RequestError as e:
            logger.exception(
                "An error occurred while processing the request",
                extra={
                    "error": str(e),
                }
            )
            return LiteLLMOutput(
                response="",
                completion_tokens=0,
            )
    
    def process(
        self,
        inputs: LiteLLMInput
    ) -> LiteLLMOutput:
        """Process the input and return the output.

        Args:
            inputs (LiteLLMInput): The input to process.

        Returns:
            LiteLLMOutput: The processed output.
        """
        
        return self._inference_llm(
            messages=inputs.messages,
            model=inputs.model if inputs.model else self.litellm_setting.model,
            response_format=inputs.response_format if inputs.response_format else None,
            temperature=inputs.temperature if inputs.temperature else self.litellm_setting.temperature,
            top_p=inputs.top_p if inputs.top_p else self.litellm_setting.top_p,
            n=inputs.n if inputs.n else self.litellm_setting.n,
            frequency_penalty=inputs.frequency_penalty if inputs.frequency_penalty else self.litellm_setting.frequency_penalty,
            max_completion_tokens=inputs.max_completion_tokens if inputs.max_completion_tokens else self.litellm_setting.max_completion_tokens,
            reasoning_effort=inputs.reasoning_effort if inputs.reasoning_effort else None,
        )
    
    async def process_async(
        self, 
        inputs: LiteLLMInput
    ) -> LiteLLMOutput:
        """Process the input and return the output.

        Args:
            inputs (LiteLLMInput): The input to process.

        Returns:
            LiteLLMOutput: The processed output.
        """
        
        return await self._inference_llm_async(
            messages=inputs.messages,
            model=inputs.model if inputs.model else self.litellm_setting.model,
            response_format=inputs.response_format if inputs.response_format else None,
            temperature=inputs.temperature if inputs.temperature else self.litellm_setting.temperature,
            top_p=inputs.top_p if inputs.top_p else self.litellm_setting.top_p,
            n=inputs.n if inputs.n else self.litellm_setting.n,
            frequency_penalty=inputs.frequency_penalty if inputs.frequency_penalty else self.litellm_setting.frequency_penalty,
            max_completion_tokens=inputs.max_completion_tokens if inputs.max_completion_tokens else self.litellm_setting.max_completion_tokens,
            reasoning_effort=inputs.reasoning_effort if inputs.reasoning_effort else None,
        )
        
    def process_embedding(
        self,
        inputs: LiteLLMEmbeddingInput
    ) -> LiteLLMEmbeddingOutput:
        """Process the input for embedding and return the output.

        Args:
            inputs (LiteLLMEmbeddingInput): The input to process.

        Returns:
            LiteLLMEmbeddingOutput: The processed output.
        """
        
        return self._embedding_llm(
            model=inputs.model,
            inputs=inputs.inputs,
        )
        
    async def process_embedding_async(
        self, 
        inputs: LiteLLMEmbeddingInput
    ) -> LiteLLMEmbeddingOutput:        
        """Asynchronously process the input for embedding and return the output.

        Args:
            inputs (LiteLLMEmbeddingInput): The input to process.

        Returns:
            LiteLLMEmbeddingOutput: The processed output.
        """
        
        return await self._embedding_llm_async(
            model=inputs.model,
            inputs=inputs.inputs,
        )
    

    def _build_payload(
        self,
        messages: Messages,
        model: str,
        response_format: type[BaseModel] | None,
        frequency_penalty: float,
        n: int,
        temperature: float,
        top_p: float,
        max_completion_tokens: int,
        reasoning_effort: str | None = None,
    ) -> dict[str, Any]:
        """Build the payload for the LiteLLM API request.

        Args:
            messages (Messages): The messages to include in the request.
            model (str): The model to use for processing.
            response_format (type[BaseModel] | None): The response format.
            frequency_penalty (float): The frequency penalty for the model.
            n (int): The number of responses to generate.
            temperature (float): The temperature for the model.
            top_p (float): The top_p value for the model.
            max_completion_tokens (int): The maximum number of completion tokens.
            reasoning_effort (str | None): The reasoning effort level.

        Returns:
            dict[str, Any]: The payload for the LiteLLM API request.
        """
        
        payload: dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "max_completion_tokens": max_completion_tokens,
            "frequency_penalty": frequency_penalty,
            "messages": self._build_messages(messages),
        }
        
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort

        if response_format:
            # Get schema with definitions dereferenced
            schema = response_format.model_json_schema(mode='serialization')
            
            # If schema has $ref, resolve it
            if '$ref' in schema and '$defs' in schema:
                ref_name = schema['$ref'].split('/')[-1]
                if ref_name in schema['$defs']:
                    # Replace root with referenced definition
                    resolved = schema['$defs'][ref_name].copy()
                    resolved['$defs'] = schema['$defs']
                    schema = resolved
            
            # Ensure additionalProperties is False at all levels
            def set_additional_properties_false(obj):
                if isinstance(obj, dict):
                    if "properties" in obj:
                        obj["additionalProperties"] = False
                    for value in obj.values():
                        set_additional_properties_false(value)
                elif isinstance(obj, list):
                    for item in obj:
                        set_additional_properties_false(item)
            
            set_additional_properties_false(schema)
            
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_format.__name__,
                    "schema": schema,
                    "strict": False  # Disable strict mode to allow optional fields
                }
            }
        
        return payload
    
    
    def _build_messages(
        self,
        messages: Messages,
    ) -> list[dict[str, Any]]:
        """Build the messages for the LiteLLM API request.

        Args:
            messages (Messages): The messages to include in the request.

        Returns:
            list[dict[str, Any]]: The messages for the LiteLLM API request.
        """
        
        built_messages: list[dict[str, Any]] = [] 
        
        for message in messages:
            built_message: dict[str, Any] = {}
            if message.image_url:
                built_message = {
                "role": message.role.value,
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": message.image_url
                        }
                    }
                ]
            }
            elif message.file_url:
                built_message = {
                    "role": message.role.value,
                    "content": [
                        {
                            "type": "file",
                            "file": {
                                "file_data": message.file_url
                            }
                        }
                    ]
                }
            else:
                built_message = {
                    "role": message.role.value,
                    "content": message.content,
                }
            
            built_messages.append(built_message)

        return built_messages