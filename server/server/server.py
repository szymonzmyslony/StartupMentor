import asyncio
import os
import re
import time
from typing import List
import instructor
from crew import agent_request
from embeddigs import embedding_request
from query_rewrite import FirstResponse, FollowUp, QueryPlan

from supabase_utils import get_supabase
from utils import (
    stream_chunk,
    streamSse,
)  # formats chunks for use with experimental_StreamData
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
import json

from dotenv import load_dotenv

load_dotenv()


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Experimental-Stream-Data"
    ],  # this is needed for streaming data header to be read by the client
)

client = OpenAI()


async def matchChunksWithinDocument(document_id: int, query: str, topK: int = 3):
    supabase = get_supabase()
    query_embedding = list(map(lambda x: x.embedding, embedding_request([query])))[0]

    result = await supabase.match_chunk_within_document(
        document_id, query_embedding, top_k=2
    )
    return result


async def match_chunks_within_documents(query: str, topK: int = 3, topN: int = 3):
    supabase = get_supabase()
    query_embedding = list(map(lambda x: x.embedding, embedding_request([query])))[0]

    result = await supabase.match_chunks_within_documents(
        query_embedding, top_k=topK, top_n=topN
    )

    return result


async def matchDocument(query: str, topK: int = 3):
    supabase = get_supabase()
    query_embedding = list(map(lambda x: x.embedding, embedding_request([query])))[0]

    result = await supabase.match_document(query_embedding, top_k=2)
    return result


system_message_query_breaking = {
    "role": "system",
    "content": "You are a top-tier query planner and startup mentor combined. Your task is to dissect founder questions into smaller, manageable queries. Think step-by-step, breaking down complex questions to understand the core issues, first principles, real world examples, and solution/problem framewroks. Always use external tools to fetch aditional information. Make sure to understand the question and provide a clear and concise answer.",
}
tools = [
    {
        "type": "function",
        "function": {
            "name": "matchChunks",
            "description": "Fetches relavant document chunks based on question",
            "parameters": {
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 3,
                        "maxItems": 10,
                        "description": "Should be an array of strings.  Will document chunks from the database based on these queries. Those should be diverse and relevant to the question and range from first principle, real world examples to solution framework. ",
                    },
                    "topK": {
                        "type": "number",
                        "description": "How many chunks to retrieve",
                    },
                },
                "required": ["query"],
            },
        },
    }
]

system_message: ChatCompletionMessageParam = {
    "role": "system",
    "content": "You are a world renowned tech startup mentor. Your job is to contextualize founder question based on their background. Think step-by-step, breaking down complex questions to understand the core issues, and real world situations. Then ask any nesssary follow up questions to get a clear and concise answer as well as return the query plan.",
}


# def query_rewrite(messages: List[ChatCompletionMessageParam]):
#     client = instructor.patch(OpenAI())
#     newMessages = [system_message] + messages
#     yield "calling instructor", "function_call"

#     response: FirstResponse = client.chat.completions.create(
#         response_format=First
#         model="gpt-3.5-0125", stream=True, messages=newMessages
#     )

#     result = response.result
#     if isinstance(result, FollowUp):
#         yield result.question
#     elif isinstance(result, QueryPlan):
#         yield result.query_graph[0].question
#     yield response


@app.post("/ask")
async def ask(req: dict):
    messages: List[ChatCompletionMessageParam] = req.get("messages")  # type: ignore

    def generator():
        try:

            # Use 'async for' to iterate over the generator's yielded values
            for response in agent_request(messages):
                # Process each response as it's yielded
                yield streamSse(response)  # or any other processing you need

        except Exception as e:
            # Handle any exceptions that might occur
            print(f"An error occurred: {e}")

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"X-Experimental-Stream-Data": "true"},
    )
