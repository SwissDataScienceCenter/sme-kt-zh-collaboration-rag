import io
import base64

import numpy as np

import torch
from transformers import CLIPProcessor, CLIPModel, CLIPTokenizer, CLIPTextModel

from PIL import Image

from conversational_toolkit.chunking.base import Chunk


class CLIPEmbeddings:
    # TODO: Update Embedding main class to support images as well, so not inheriting it now.

    def __init__(self):
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-base-patch32")
        self.text_model = CLIPTextModel.from_pretrained("openai/clip-vit-base-patch32")

    async def get_text_embeddings(self, texts: str | list[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]

        inputs = self.tokenizer(
            texts, return_tensors="pt", padding=True, truncation=True
        )

        with torch.no_grad():
            text_embeddings = self.text_model(**inputs).pooler_output

        return text_embeddings.squeeze().numpy()

    async def get_image_embeddings(self, images: str | list[str]) -> np.ndarray:
        if isinstance(images, str):
            images = [images]

        decoded_images = []
        for img_base64 in images:
            img_data = base64.b64decode(img_base64)
            img = Image.open(io.BytesIO(img_data))
            decoded_images.append(img)

        image_inputs = self.processor(
            images=decoded_images, return_tensors="pt", padding=True
        )

        with torch.no_grad():
            image_embeddings = self.clip_model.get_image_features(**image_inputs)

        return image_embeddings.squeeze().numpy()

    async def get_embeddings(self, chunks: str | Chunk | list[Chunk]) -> np.ndarray:

        if isinstance(chunks, str):
            chunks = [Chunk(content=chunks, mime_type="text/plain", title="Query")]

        if isinstance(chunks, Chunk):
            chunks = [chunks]

        embeddings_l = []

        for chunk in chunks:
            if chunk.mime_type.startswith("text"):
                embeddings_l.append(await self.get_text_embeddings(chunk.content))
            elif chunk.mime_type.startswith("image"):
                embeddings_l.append(await self.get_image_embeddings(chunk.content))
            else:
                raise ValueError("Unknown Data Type")

        combined_embeddings = np.array(embeddings_l)

        return combined_embeddings
