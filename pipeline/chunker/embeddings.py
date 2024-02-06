from openai import OpenAI

import os

from dotenv import load_dotenv
import numpy as np

load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embedding(text, model="text-embedding-3-small"):
    response = client.embeddings.create(input=text, model=model)

    return response.data


def get_indices_above_threshold(distances, breakpoint_percentile_threshold):
    breakpoint_distance_threshold = np.percentile(
        distances, breakpoint_percentile_threshold
    )
    indices_above_thresh = [
        i for i, x in enumerate(distances) if x > breakpoint_distance_threshold
    ]  # The indices of those breakpoints on your list
    return indices_above_thresh
