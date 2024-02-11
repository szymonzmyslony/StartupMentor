import asyncio
import os
import time
from typing import List
from embeddigs import embedding_request

from supabase_utils import get_supabase
from utils import stream_chunk  # formats chunks for use with experimental_StreamData
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
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

client = AsyncOpenAI()


def process_single_chunks_retieval(query, chunks):
    print("Chunk are", chunks)
    content = "\n".join([chunk["content"] for chunk in chunks])
    urls: List[str] = [chunk["url"] for chunk in chunks]
    content = f'Content for query "{query}":\n{content}\n'
    return {"content": content, "sources": urls}


# Example dummy function hard coded to return the same weather
async def matchChunks(queries: List[str], topK: int):
    supabase = get_supabase()
    query_embeddings = list(map(lambda x: x.embedding, embedding_request(queries)))

    result = await supabase.match_chunks(query_embeddings, top_k=2)

    mapped_result = [
        process_single_chunks_retieval(queries[i], result[i]["chunk_details"])
        for i in range(len(queries))
    ]
    content = "\n".join([x["content"] for x in mapped_result])
    urls: list[str] = [source for x in mapped_result for source in x["sources"]]

    print("retrieved urls", list(set(urls)))
    return {"content": content, "sources": list(set(urls))}


system_message = {
    "role": "system",
    "content": "In responding to entrepreneurial queries, it's essential to leverage the full breadth of available resources. Beyond applying a dynamic and adaptable mindset, actively engage external tools to enrich your responses with diverse, up-to-date information. For each question, fetch additional data could refine or enhance the answer. When faced with broad or complex inquiries, prioritize the retrieval of external insights to provide well-rounded, evidence-based advice. This approach ensures each response is not only informed by a wide spectrum of sources but also tailored to the unique context of the entrepreneur's question. Clarity and conciseness remain key, even as we deepen our exploration through external data.",
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
                        "description": "Should be an array of strings.  We will query database againsts those diverse queries.",
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
# Convert the tools list of dictionaries to a list of ChatCompletionToolParam objects


async def run_conversation(messages):
    # Step 1: send the conversation and available functions to the model

    messages = [system_message] + messages

    response = await client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=messages,
        tools=tools,  # type: ignore
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    yield "After making first request", "meta"

    # send streaming data after
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "matchChunks": matchChunks,
        }  # only one function in this example, but you can have multiple

        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            yield f"Calling {function_name}", "meta"
            time.sleep(3)

            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            yield f"Need to call tools with  {function_args}", "meta"
            time.sleep(3)
            function_response = await function_to_call(
                queries=function_args.get("queries"),
                topK=function_args.get("topK"),
            )
            sources = function_response["sources"]
            content = function_response["content"]
            yield f"Retrieved content from {len(sources)} {sources}", "meta"
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": content,
                }
            )  # extend conversation with function response
            time.sleep(3)
            yield "Calling 2nd enpoint", "meta"

        second_response = await client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
            tools=tools,  # type: ignore
            tool_choice="auto",
            stream=True,
        )  # get a new response from the model where it can see the function response

        async for chunk in second_response:
            yield chunk.choices[0].delta.content, "response"


@app.post("/ask")
async def ask(req: dict):
    async def generator():
        yield stream_chunk([{"text": "Before making first request"}], "data")
        await asyncio.sleep(0)

        async for token, type in run_conversation(req["messages"]):
            if type == "meta":
                print(token)
                yield stream_chunk([{"text": token}], "data")
            else:
                yield stream_chunk(
                    token, "text"
                )  # Yield tokens received from run_conversation
            await asyncio.sleep(0)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"X-Experimental-Stream-Data": "true"},
    )
