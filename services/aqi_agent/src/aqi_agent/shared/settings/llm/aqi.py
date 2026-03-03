from __future__ import annotations

from lite_llm import LiteLLMSetting


class AqiLLMSettings(LiteLLMSetting):
    opensearch_top_k: int = 10
