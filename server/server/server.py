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
    streamSse,
    yield_in_thread,
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


@app.post("/ask")
async def ask(req: dict):
    messages: List[ChatCompletionMessageParam] = req.get("messages")  # type: ignore

    def generator():
        try:

            # Use 'async for' to iterate over the generator's yielded values
            for response in agent_request(messages):
                # Process each response as it's yielded
                yield response

        except Exception as e:
            # Handle any exceptions that might occur
            print(f"An error occurred: {e}")

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"X-Experimental-Stream-Data": "true"},
    )
