from conversational_toolkit.chunking.base import Chunker, Chunk


class SpecificCharChunker(Chunker):
    def split_on_character(self, text: str, split_character: str) -> list[str]:
        """Splits the text on the specified character."""
        return text.split(split_character)

    def split_on_nb_characters(
        self, text: str, max_number_of_characters: int
    ) -> list[str]:
        """Splits the text into chunks of a specified maximum number of characters."""
        return [
            text[i : i + max_number_of_characters]
            for i in range(0, len(text), max_number_of_characters)
        ]

    def make_chunks(
        self,
        split_characters: list[str],
        document_to_text: dict[str, str],
        max_number_of_characters: int,
    ) -> list[Chunk]:
        """Splits the text into chunks of a specified maximum number of characters, with a specified overlap between chunks."""

        chunk_cnt = 0

        chunks_to_split: list[Chunk] = []
        chunks: list[Chunk] = []

        chunks_to_split.append(
            Chunk(
                title="0",
                mime_type="text/markdown",
                content=document_to_text["alexnet_paper.pdf"],
                metadata={"doc_title": "alexnet_paper.pdf"},
            )
        )

        for split_character in split_characters:
            # for each chunk in chunks_to_split, split it using the split_char
            # then, if it is too small, remove it from chunks_to_split and add it to chunks
            for chunk in chunks_to_split:
                split_chunks = self.split_on_character(chunk.content, split_character)

                for split_chunk in split_chunks:
                    if len(split_chunk) <= max_number_of_characters:
                        chunks.append(
                            Chunk(
                                title=str(chunk_cnt),
                                mime_type="text/markdown",
                                content=split_chunk,
                                metadata={"doc_title": chunk.metadata["doc_title"]},
                            )
                        )
                        chunk_cnt += 1
                    else:
                        chunks_to_split.append(
                            Chunk(
                                title=str(chunk_cnt),
                                mime_type="text/markdown",
                                content=split_chunk,
                                metadata={"doc_title": chunk.metadata["doc_title"]},
                            )
                        )
                        chunk_cnt += 1

                # remove the original chunk from chunks_to_split
                chunks_to_split.remove(chunk)

        # for each chunk still in chunks_to_split, split it using the split_char
        # and move them to chunks
        for chunk in chunks_to_split:
            split_chunks = self.split_on_nb_characters(
                chunk.content, max_number_of_characters
            )

            for split_chunk in split_chunks:
                chunks.append(
                    Chunk(
                        title=str(chunk_cnt),
                        mime_type="text/markdown",
                        content=split_chunk,
                        metadata={"doc_title": chunk.metadata["doc_title"]},
                    )
                )
                chunk_cnt += 1

        # Remove any void chunks
        chunks = [chunk for chunk in chunks if chunk.content.strip() != ""]

        return chunks
