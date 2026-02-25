# WARNING: CODE NOT CHECKED!! (ChatGPT mainly coded for a hackathon)
# TODO: Check the code before any push in project

import io
import base64
from typing import Any, Optional

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from qwen_vl_utils.vision_process import process_vision_info
from transformers.models.qwen3_vl.processing_qwen3_vl import Qwen3VLProcessor
from transformers.models.qwen3_vl.modeling_qwen3_vl import (
    Qwen3VLModel,
    Qwen3VLConfig,
    Qwen3VLPreTrainedModel,
)

from dataclasses import dataclass
from transformers.modeling_outputs import ModelOutput

from conversational_toolkit.chunking.base import Chunk


# --- Minimal "embedding-only" model head (matches the HF repo script idea) ---
@dataclass
class Qwen3VLForEmbeddingOutput(ModelOutput):
    last_hidden_state: Optional[torch.FloatTensor] = None
    attention_mask: Optional[torch.Tensor] = None


class Qwen3VLForEmbedding(Qwen3VLPreTrainedModel):
    _checkpoint_conversion_mapping = {}
    accepts_loss_kwargs = False
    config: Qwen3VLConfig

    def __init__(self, config: Qwen3VLConfig):
        super().__init__(config)
        self.model = Qwen3VLModel(config)
        self.post_init()

    def forward(
        self,
        input_ids: torch.LongTensor = None,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[Any] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        pixel_values: Optional[torch.Tensor] = None,
        pixel_values_videos: Optional[torch.FloatTensor] = None,
        image_grid_thw: Optional[torch.LongTensor] = None,
        video_grid_thw: Optional[torch.LongTensor] = None,
        cache_position: Optional[torch.LongTensor] = None,
        **kwargs,
    ) -> Qwen3VLForEmbeddingOutput:
        outputs = self.model(
            input_ids=input_ids,
            pixel_values=pixel_values,
            pixel_values_videos=pixel_values_videos,
            image_grid_thw=image_grid_thw,
            video_grid_thw=video_grid_thw,
            position_ids=position_ids,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            cache_position=cache_position,
            **kwargs,
        )
        return Qwen3VLForEmbeddingOutput(
            last_hidden_state=outputs.last_hidden_state,
            attention_mask=attention_mask,
        )


# --- Embedder wrapper (same algorithm as scripts/qwen3_vl_embedding.py) ---
class _Qwen3VLEmbedder:
    def __init__(
        self,
        model_name_or_path: str = "Qwen/Qwen3-VL-Embedding-2B",
        *,
        instruction: str = "Represent the user's input.",
        max_length: int = 8192,
        normalize: bool = True,
        output_dim: Optional[
            int
        ] = None,  # 64..2048 supported by the model (MRL); we slice.
        torch_dtype: Optional[torch.dtype] = None,
        attn_implementation: Optional[str] = None,  # e.g. "flash_attention_2"
        device: Optional[str] = None,
        min_pixels: int = 4 * (16 * 2) * (16 * 2),
        max_pixels: int = 1800 * (16 * 2) * (16 * 2),
        trust_remote_code: bool = True,
    ):
        self.max_length = max_length
        self.instruction = instruction
        self.normalize = normalize
        self.output_dim = output_dim
        self.min_pixels = min_pixels
        self.max_pixels = max_pixels

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)

        model_kwargs = {}
        if torch_dtype is not None:
            model_kwargs["torch_dtype"] = torch_dtype
        if attn_implementation is not None:
            model_kwargs["attn_implementation"] = attn_implementation

        self.model = Qwen3VLForEmbedding.from_pretrained(
            model_name_or_path,
            trust_remote_code=trust_remote_code,
            **model_kwargs,
        ).to(self.device)
        self.model.eval()

        self.processor = Qwen3VLProcessor.from_pretrained(
            model_name_or_path, padding_side="right"
        )

    @staticmethod
    def _pool_last_token(
        hidden_state: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        # pick the final "1" position per row in attention_mask
        flipped = attention_mask.flip(dims=[1])
        last_one_from_end = flipped.argmax(dim=1)
        col = attention_mask.shape[1] - last_one_from_end - 1
        row = torch.arange(hidden_state.shape[0], device=hidden_state.device)
        return hidden_state[row, col]

    def _format_conversation(
        self,
        *,
        text: Optional[str] = None,
        image: Optional[Image.Image] = None,
        instruction: Optional[str] = None,
    ) -> list[dict]:
        inst = (instruction or self.instruction).strip()
        if inst and inst[-1] not in ".!?;:":
            inst += "."

        content = []
        if image is not None:
            content.append(
                {
                    "type": "image",
                    "image": image,
                    "min_pixels": self.min_pixels,
                    "max_pixels": self.max_pixels,
                }
            )
        content.append({"type": "text", "text": text or ""})

        return [
            {"role": "system", "content": [{"type": "text", "text": inst}]},
            {"role": "user", "content": content},
        ]

    def _preprocess(self, conversations: list[list[dict]]) -> dict[str, torch.Tensor]:
        text = self.processor.apply_chat_template(
            conversations, add_generation_prompt=True, tokenize=False
        )

        images, videos, video_kwargs = None, None, {"do_sample_frames": False}
        # Vision parsing (image/video tokens, grids, etc.)
        images, video_inputs, video_kwargs = process_vision_info(
            conversations,
            image_patch_size=16,
            return_video_metadata=True,
            return_video_kwargs=True,
        )

        if video_inputs is not None:
            videos, video_metadata = zip(*video_inputs)
            videos = list(videos)
            video_metadata = list(video_metadata)
        else:
            videos, video_metadata = None, None

        inputs = self.processor(
            text=text,
            images=images,
            videos=videos,
            video_metadata=video_metadata,
            truncation=True,
            max_length=self.max_length,
            padding=True,
            do_resize=False,
            return_tensors="pt",
            **video_kwargs,
        )
        return {k: v.to(self.device) for k, v in inputs.items()}

    @torch.no_grad()
    def encode(
        self,
        items: list[dict],
        *,
        normalize: Optional[bool] = None,
        output_dim: Optional[int] = None,
    ) -> torch.Tensor:
        conversations = [
            self._format_conversation(
                text=it.get("text"),
                image=it.get("image"),
                instruction=it.get("instruction"),
            )
            for it in items
        ]

        model_inputs = self._preprocess(conversations)
        outputs = self.model(**model_inputs)

        emb = self._pool_last_token(
            outputs.last_hidden_state, model_inputs["attention_mask"]
        )

        # Optional Matryoshka slicing (model is trained to support multiple dims)
        od = output_dim if output_dim is not None else self.output_dim
        if od is not None:
            emb = emb[:, :od]

        do_norm = self.normalize if normalize is None else normalize
        if do_norm:
            emb = F.normalize(emb, p=2, dim=-1)
        return emb


# --- Your CLIP-like facade ---
class Qwen3VLEmbeddings:
    # TODO: Update Embedding main class to support images as well, so not inheriting it now.

    def __init__(
        self,
        model_name_or_path: str = "Qwen/Qwen3-VL-Embedding-2B",
        *,
        instruction: str = "Represent the user's input.",
        output_dim: int | None = None,
        normalize: bool = True,
        torch_dtype: torch.dtype | None = None,  # e.g. torch.float16
        attn_implementation: str | None = None,  # e.g. "flash_attention_2"
        device: str | None = None,
    ):
        self.embedder = _Qwen3VLEmbedder(
            model_name_or_path=model_name_or_path,
            instruction=instruction,
            output_dim=output_dim,
            normalize=normalize,
            torch_dtype=torch_dtype,
            attn_implementation=attn_implementation,
            device=device,
        )

    async def get_text_embeddings(self, texts: str | list[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        items = [{"text": t} for t in texts]
        emb = self.embedder.encode(items)
        return emb.detach().cpu().numpy()

    async def get_image_embeddings(self, images: str | list[str]) -> np.ndarray:
        if isinstance(images, str):
            images = [images]

        decoded_images: list[Image.Image] = []
        for img_base64 in images:
            img_data = base64.b64decode(img_base64)
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            decoded_images.append(img)

        items = [{"image": im, "text": ""} for im in decoded_images]
        emb = self.embedder.encode(items)
        return emb.detach().cpu().numpy()

    async def get_embeddings(self, chunks: str | Chunk | list[Chunk]) -> np.ndarray:
        if isinstance(chunks, str):
            chunks = [Chunk(content=chunks, mime_type="text/plain", title="Query")]

        if isinstance(chunks, Chunk):
            chunks = [chunks]

        items: list[dict] = []
        for chunk in chunks:
            if chunk.mime_type.startswith("text"):
                items.append({"text": chunk.content})
            elif chunk.mime_type.startswith("image"):
                # chunk.content is base64 in your current design
                img_data = base64.b64decode(chunk.content)
                img = Image.open(io.BytesIO(img_data)).convert("RGB")
                items.append({"image": img, "text": ""})
            else:
                raise ValueError(f"Unknown Data Type: {chunk.mime_type}")

        emb = self.embedder.encode(items)
        return emb.detach().cpu().numpy()
