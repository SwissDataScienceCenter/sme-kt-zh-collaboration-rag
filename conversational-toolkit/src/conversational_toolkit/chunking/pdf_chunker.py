import os
import shutil
import io
import base64
import re
from enum import StrEnum

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption
from docling_core.types.doc.document import PictureItem
from pathlib import Path
from markitdown import MarkItDown  # type: ignore[import-untyped]
from PIL import Image  # type: ignore[import-untyped]

from conversational_toolkit.chunking.base import Chunk, Chunker


class MarkdownConverterEngine(StrEnum):
    MARKITDOWN = "markitdown"
    DOCLING = "docling"


class PDFChunker(Chunker):
    # TODO: Improve by not creating temporary files for images and support more image formats
    # TODO: Currently resizing, maybe not desired.

    def _pdf2markdown(
        self,
        file_path: str,
        engine: MarkdownConverterEngine = MarkdownConverterEngine.DOCLING,
        write_images: bool = False,
        image_path: str | None = None,
    ) -> str:
        if engine == MarkdownConverterEngine.MARKITDOWN:
            if write_images:
                raise NotImplementedError("Image extraction is not supported with MarkItDown engine.")
            result = MarkItDown().convert(file_path)
            return str(result.text_content)
        elif engine == MarkdownConverterEngine.DOCLING:
            if write_images and image_path:
                pipeline_options = PdfPipelineOptions()
                pipeline_options.generate_picture_images = True

                doc_converter = DocumentConverter(
                    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
                )
                conv_result = doc_converter.convert(file_path)

                # Manually save images from PictureItem elements
                doc_filename = Path(file_path).stem
                picture_counter = 0
                for element, _level in conv_result.document.iterate_items():
                    if isinstance(element, PictureItem) and element.image:
                        picture_counter += 1
                        image_filename = Path(image_path) / f"{doc_filename}-picture-{picture_counter}.png"
                        with open(image_filename, "wb") as fp:
                            element.image.pil_image.save(fp, format="PNG")

                return conv_result.document.export_to_markdown()  # type: ignore[no-any-return]
            else:
                return DocumentConverter().convert(file_path).document.export_to_markdown()  # type: ignore[no-any-return]
        else:
            raise NotImplementedError(f"Engine '{engine}' is not supported.")

    def _normalize_newlines(self, text: str) -> str:
        paragraphs = text.split("\n\n")
        processed_paragraphs = [para.replace("\n", " ") for para in paragraphs]
        return "\n\n".join(processed_paragraphs)

    def make_chunks(
        self,
        file_path: str,
        engine: MarkdownConverterEngine = MarkdownConverterEngine.DOCLING,
        write_images: bool = True,
        image_path: str | None = "./tmp",
    ) -> list[Chunk]:
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        markdown = self._pdf2markdown(file_path, engine, write_images=write_images, image_path=image_path)
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
                        base64_encoding = base64.b64encode(buffered.getvalue()).decode("utf-8")

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
