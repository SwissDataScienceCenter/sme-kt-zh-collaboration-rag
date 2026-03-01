from loguru import logger
import numpy as np
from numpy.typing import NDArray

from conversational_toolkit.embeddings.base import EmbeddingsModel
from openai import AsyncOpenAI


class OpenAIEmbeddings(EmbeddingsModel):
    """
    OpenAI embeddings model.

    Attributes:
        model_name (str): The name of the embeddings model.
    """

    def __init__(self, model_name: str):
        self.client = AsyncOpenAI()
        self.model_name = model_name
        logger.debug(f"OpenAI embeddings model loaded: {model_name}")

    async def get_embeddings(
        self, texts: str | list[str], batch_size: int = 100, max_chars: int = 30_000
    ) -> NDArray[np.float64]:
        """Embed one or more texts using OpenAI, batching requests to stay within the token-per-request limit."""
        if isinstance(texts, str):
            texts = [texts]

        texts = [t[:max_chars] if len(t) > max_chars else t for t in texts]
        batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
        all_embeddings: list[NDArray[np.float64]] = []
        for batch in batches:
            response = await self.client.embeddings.create(input=batch, model=self.model_name, dimensions=1024)
            all_embeddings.append(np.asarray([d.embedding for d in response.data]))

        embeddings = np.concatenate(all_embeddings, axis=0)
        logger.info(f"OpenAI embeddings shape: {embeddings.shape}")
        return embeddings
