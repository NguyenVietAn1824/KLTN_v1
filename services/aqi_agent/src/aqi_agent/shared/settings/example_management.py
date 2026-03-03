from __future__ import annotations

from base import BaseModel


class ExampleManagementSettings(BaseModel):
    index_name: str = 'examples'
    knn_size: int = 10
    dimensions: int = 1536
    embedding_model: str = 'gemini-embedding'
    encoding_format: str = 'float'
    threshold: float = 0.8
