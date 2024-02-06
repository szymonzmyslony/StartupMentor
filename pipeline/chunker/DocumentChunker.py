import math
from chunker.clean_document import MAX_LENGTH, process_document
from chunker.embeddings import get_embedding, get_indices_above_threshold
from chunker.openai_utils import num_tokens_from_string
from chunker.similarity import calculate_cosine_distances
import numpy as np


class DocumentChunker:
    def __init__(self, document, title, description, logger):
        self.chunks = []
        processed_document, is_sections = process_document(document)
        chunks = list(map(lambda x: x["text"], processed_document))
        self.titles = list(map(lambda x: x["title"], processed_document))
        logger(f"Has returned md secitons {is_sections} paragraphs from the document.")
        self.chunks = chunks
        self.paragraphs = chunks
        self.has_meanigful_sections = is_sections
        self.logger = logger
        self.title = title
        self.description = description

    def get_dynamic_breakpoint_percentile(
        self, min_threshold=80, max_threshold=97, max_paragraphs=100
    ):
        num_paragraphs = max(
            1, len(self.paragraphs)
        )  # Ensure num_paragraphs is at least 1
        log_scale = math.log(num_paragraphs + 1, max_paragraphs + 1)
        dynamic_threshold = min_threshold + (max_threshold - min_threshold) * log_scale
        return min(dynamic_threshold, max_threshold)

    def batch_paragraphs(self, paragraphs, max_tokens=8192):
        all_batches = []
        current_batch, current_batch_tokens = [], 0

        for paragraph in paragraphs:
            paragraph_tokens = num_tokens_from_string(paragraph)

            if paragraph_tokens > max_tokens:
                # Handle oversized paragraphs by either splitting them or deciding to process them individually
                # For simplicity, we'll add oversized paragraphs in a batch on their own
                if current_batch:  # Ensure the current batch is not empty
                    all_batches.append(current_batch)  # Save the current batch
                    current_batch, current_batch_tokens = (
                        [],
                        0,
                    )  # Reset for the next batch

                all_batches.append(
                    [paragraph]
                )  # Add the oversized paragraph in its own batch
                self.logger(
                    f"Paragraph exceeds token limit, processed individually: {paragraph[:30]}..."
                )
                continue  # Skip to the next paragraph

            if current_batch_tokens + paragraph_tokens <= max_tokens:
                current_batch.append(paragraph)
                current_batch_tokens += paragraph_tokens
            else:
                all_batches.append(current_batch)  # Current batch is full, save it
                current_batch, current_batch_tokens = [
                    paragraph
                ], paragraph_tokens  # Start a new batch with the current paragraph

        if current_batch:  # Don't forget to add the last batch if it has any paragraphs
            all_batches.append(current_batch)

        return all_batches

    def embed_paragraphs(self):

        batches = self.batch_paragraphs(self.paragraphs)
        all_embeddings = []
        for batch in batches:
            batch_embeddings = [x.embedding for x in get_embedding(batch)]
            all_embeddings.extend(batch_embeddings)
        self.embeddings = all_embeddings

    def calculate_distances_and_chunk(
        self, max_chunk_length=MAX_LENGTH * 1.5, min_chunk_length=250
    ):
        distances = calculate_cosine_distances(self.embeddings)
        threshold = self.get_dynamic_breakpoint_percentile()
        indices_above_thresh = get_indices_above_threshold(
            distances, breakpoint_percentile_threshold=threshold
        )
        print(f"We got indices {len(indices_above_thresh)}")

        self.chunks = []
        start_index = 0
        current_chunk_length = 0

        for index, paragraph in enumerate(self.paragraphs):
            paragraph = paragraph.strip()
            paragraph_length = len(paragraph)
            new_chunk_length = (
                current_chunk_length + paragraph_length + 1
            )  # +1 for the space

            # Finalize the current chunk if needed
            if new_chunk_length > max_chunk_length or (
                indices_above_thresh and index == indices_above_thresh[0]
            ):
                if (
                    current_chunk_length >= min_chunk_length
                ):  # Finalize the current chunk
                    self.chunks.append(
                        " ".join(self.paragraphs[start_index:index]).strip()
                    )
                    start_index = index
                    current_chunk_length = paragraph_length
                else:  # Extend the current chunk if below min length
                    current_chunk_length = new_chunk_length

                if (
                    indices_above_thresh and index == indices_above_thresh[0]
                ):  # Remove the used index
                    indices_above_thresh.pop(0)
            else:
                current_chunk_length = new_chunk_length

        # Handle the last chunk
        if start_index < len(self.paragraphs):
            final_chunk = " ".join(self.paragraphs[start_index:]).strip()
            if len(final_chunk) >= min_chunk_length or not self.chunks:
                self.chunks.append(final_chunk)
            else:
                # If the final chunk is too small and there are previous chunks, extend the last chunk
                self.chunks[-1] = " ".join([self.chunks[-1], final_chunk]).strip()

        self.logger(
            f"Generated {len(self.chunks)} chunks from {len(self.paragraphs)} paragraphs."
        )

    def chunk_document(self):
        if self.has_meanigful_sections:
            return self.chunks, self.titles
        self.logger("Going into emedding mode")
        self.embed_paragraphs()
        self.calculate_distances_and_chunk()
        return self.chunks, self.titles
