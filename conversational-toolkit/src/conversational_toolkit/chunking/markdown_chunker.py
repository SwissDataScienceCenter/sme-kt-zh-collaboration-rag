from pathlib import Path

from conversational_toolkit.chunking.pdf_chunker import MarkdownConverterEngine, PDFChunker


class MarkdownChunker(PDFChunker):
    """Chunks Markdown and plain-text (.md, .txt) files using the same
    header-based logic as PDFChunker, but skips the PDF-to-Markdown
    conversion step by reading the file directly as UTF-8 text.
    """

    def _pdf2markdown(
        self,
        file_path: str,
        engine: MarkdownConverterEngine = MarkdownConverterEngine.PYMUPDF4LLM,
        write_images: bool = False,
        image_path: str | None = None,
    ) -> str:
        return Path(file_path).read_text(encoding="utf-8")
