"""Shared embedding contracts.

The canonical protocol lives in `validators.knowledge.enricher` so existing
enrichment code and new embedding backends use exactly the same request and
response objects:

- `EmbeddingRequest(node_id, content_hash, privacy_mode, text)`
- `EmbeddingResponse(vector, dimensions, tokens_used=0, model='')`
- `EmbeddingBackend.embed(request) -> EmbeddingResponse`
"""

from validators.knowledge.enricher import EmbeddingBackend, EmbeddingRequest, EmbeddingResponse

__all__ = ["EmbeddingBackend", "EmbeddingRequest", "EmbeddingResponse"]
