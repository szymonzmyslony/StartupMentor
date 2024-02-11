import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential


EMBEDDING_MODEL = "text-embedding-3-small"
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def embedding_request(text: list[str]):
    response = client.embeddings.create(input=text, model=EMBEDDING_MODEL)
    return response.data
