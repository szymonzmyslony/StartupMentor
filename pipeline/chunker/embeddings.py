from chunker.openai_utils import num_tokens_from_string
import numpy as np
from openai import OpenAI

import os

from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_indices_above_threshold(distances, breakpoint_percentile_threshold):
    breakpoint_distance_threshold = np.percentile(
        distances, breakpoint_percentile_threshold
    )
    indices_above_thresh = [
        i for i, x in enumerate(distances) if x > breakpoint_distance_threshold
    ]  # The indices of those breakpoints on your list
    return indices_above_thresh


def get_embedding(text, model="text-embedding-3-small"):
    response = client.embeddings.create(input=text, model=model, timeout=20)

    return response.data


def batch_paragraphs(paragraphs, logger, max_tokens=2000):
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
            logger(
                f"Paragraph exceeds token limit, processed individually: {paragraph[:30]} {paragraph[-100:-50]}..."
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
