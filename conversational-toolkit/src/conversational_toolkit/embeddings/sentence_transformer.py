from typing import Union, Any
from loguru import logger
from numpy._typing import NDArray
from sentence_transformers.models import Transformer, Pooling
from sentence_transformers import SentenceTransformer
from conversational_toolkit.embeddings.base import EmbeddingsModel
import numpy as np


class CustomizeSentenceTransformer(SentenceTransformer):  # type:ignore
    def _load_auto_model(
        self,
        model_name_or_path: str,
        token: bool | str | None = None,
        cache_folder: str | None = None,
        revision: str | None = None,
        trust_remote_code: bool = False,
        local_files_only: bool = False,
        model_kwargs: dict[str, Any] | None = None,
        tokenizer_kwargs: dict[str, Any] | None = None,
        config_kwargs: dict[str, Any] | None = None,
        has_modules: bool = False,
    ) -> list[Any]:
        """Creates a simple Transformer + CLS Pooling model and returns the modules. config_kwargs and has_modules are not applicable to Transformer construction and are ignored."""
        combined_model_args = {
            "token": token,
            "trust_remote_code": trust_remote_code,
            "revision": revision,
            "local_files_only": local_files_only,
            **(model_kwargs or {}),
        }
        combined_tokenizer_args = {
            "token": token,
            "trust_remote_code": trust_remote_code,
            "revision": revision,
            "local_files_only": local_files_only,
            **(tokenizer_kwargs or {}),
        }
        transformer_model = Transformer(
            model_name_or_path,
            cache_dir=cache_folder,
            model_args=combined_model_args,
            tokenizer_args=combined_tokenizer_args,
        )
        pooling_model = Pooling(transformer_model.get_word_embedding_dimension(), "cls")
        return [transformer_model, pooling_model]


class SentenceTransformerEmbeddings(EmbeddingsModel):
    def __init__(self, model_name: str, **kwargs: Any):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, **kwargs)
        self.model.eval()
        logger.debug(f"Sentence Transformer embeddings model loaded: {model_name} with kwargs: {kwargs}")

    async def get_embeddings(self, texts: Union[str, list[str]], **kwargs_encode: Any) -> NDArray[np.float64]:
        """Encode a string or a list of strings into embeddings using the model."""
        # Encode the texts using the model
        embedded_chunk = self.model.encode(texts, **kwargs_encode)

        # If a single string is given, convert the output to a numpy array of numpy arrays
        if isinstance(texts, str):
            embedded_chunk = np.array([embedded_chunk])

        logger.debug(f"{self.model_name} embeddings size: {embedded_chunk.shape}")
        return embedded_chunk  # type: ignore
