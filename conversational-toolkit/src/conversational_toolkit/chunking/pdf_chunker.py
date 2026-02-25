import os
import shutil
import io
import base64
import re
from enum import StrEnum

import pymupdf4llm  # type: ignore[import-untyped]
from markitdown import MarkItDown  # type: ignore[import-untyped]
from PIL import Image  # type: ignore[import-untyped]

from conversational_toolkit.chunking.base import Chunk, Chunker


class MarkdownConverterEngine(StrEnum):
    PYMUPDF4LLM = "pymupdf4llm"
    MARKITDOWN = "markitdown"


class PDFChunker(Chunker):
    # TODO: Improve by not creating temporary files for images and support more image formats
    # TODO: Currently resizing, maybe not desired.

    def _pdf2markdown(
        self,
        file_path: str,
        engine: MarkdownConverterEngine = MarkdownConverterEngine.PYMUPDF4LLM,
        write_images: bool = False,
        image_path: str | None = None,
    ) -> str:
        if engine == MarkdownConverterEngine.PYMUPDF4LLM:
            kwargs: dict = {}
            if write_images:
                kwargs["write_images"] = True
                if image_path:
                    kwargs["image_path"] = image_path
            return pymupdf4llm.to_markdown(file_path, **kwargs)  # type: ignore[no-any-return]
        elif engine == MarkdownConverterEngine.MARKITDOWN:
            if write_images:
                raise NotImplementedError(
                    "Image extraction is not supported with MarkItDown engine."
                )
            result = MarkItDown().convert(file_path)
            return result.text_content
        else:
            raise NotImplementedError(f"Engine '{engine}' is not supported.")

    def _normalize_newlines(self, text: str) -> str:
        paragraphs = text.split("\n\n")
        processed_paragraphs = [para.replace("\n", " ") for para in paragraphs]
        return "\n\n".join(processed_paragraphs)

    def make_chunks(
        self,
        file_path: str,
        engine: MarkdownConverterEngine = MarkdownConverterEngine.PYMUPDF4LLM,
        write_images: bool = False,
        image_path: str | None = None,
    ) -> list[Chunk]:
        markdown = self._pdf2markdown(
            file_path, engine, write_images=write_images, image_path=image_path
        )

        header_pattern = re.compile(r"^(#{1,6}\s.*)$", re.MULTILINE)
        matches = list(header_pattern.finditer(markdown))

        chunks: list[Chunk] = []
        current_chapters: list[str] = []

        if not matches:
            processed_text = self._normalize_newlines(markdown)
            chunk = Chunk(
                title="",
                content=processed_text,
                mime_type="text/markdown",
                metadata={"chapters": []},
            )
            return [chunk]

        for i, match in enumerate(matches):
            header_line = match.group(1).strip()
            header_level = header_line.count("#", 0, header_line.find(" "))

            if len(current_chapters) < header_level:
                current_chapters.append(header_line)
            else:
                current_chapters = [*current_chapters[: header_level - 1], header_line]

            start_idx = match.start()
            if i < len(matches) - 1:
                end_idx = matches[i + 1].start()
            else:
                end_idx = len(markdown)
            chunk_text = markdown[start_idx:end_idx]

            processed_chunk_text = self._normalize_newlines(chunk_text)

            chunk = Chunk(
                title=header_line,
                content=processed_chunk_text,
                mime_type="text/markdown",
                metadata={"chapters": current_chapters.copy()},
            )
            chunks.append(chunk)

        if write_images and image_path:
            for file_name in os.listdir(image_path):
                extension = os.path.splitext(file_name)[1].lower()
                if extension in [".png", ".jpg", ".jpeg", ".gif"]:
                    image_file_path = os.path.join(image_path, file_name)
                    with Image.open(image_file_path) as img:
                        buffered = io.BytesIO()
                        img.save(buffered, format=img.format)
                        base64_encoding = base64.b64encode(buffered.getvalue()).decode(
                            "utf-8"
                        )

                    image_chunk = Chunk(
                        title=file_name,
                        content=base64_encoding,
                        mime_type=f"image/{extension[1:]}",
                        metadata={"chapters": []},
                    )
                    chunks.append(image_chunk)

        if write_images and image_path:
            shutil.rmtree(image_path)

        return chunks
