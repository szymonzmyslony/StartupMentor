import asyncio
from asyncore import loop
from concurrent.futures import ThreadPoolExecutor
import json
from typing import Generator
from openai import OpenAI
from tenacity import retry, sleep, stop_after_attempt, wait_random_exponential
from query_rewrite import FollowUp, query_rewrite
from summarize_data import summarize_startup_context
from tools import matchChunks, sync_match_chunks, tools
from utils import streamSse


GPT_MODEL = "gpt-3.5-turbo-0125"

client = OpenAI()


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def agent_request(
    messages, functions=None, model=GPT_MODEL
) -> Generator[str, None, None]:
    print("messages are:", messages)
    yield streamSse("Making first request", "data")

    response = query_rewrite(messages)

    result = response.result

    yield streamSse("Received data from instructor", "data")

    if isinstance(result, FollowUp):
        yield streamSse(result.question, "text")

        return

    else:
        queries = [query.question for query in result.query_graph]
        yield streamSse("Fetching queries first message", "data")

        fetched_data = sync_match_chunks(queries, 3)

        response = summarize_startup_context(messages, fetched_data)
        for r in response:
            yield streamSse(r, "data")
        return

    #     tool_calls = response_message.tool_calls

    #     # Step 2: check if the model wanted to call a function
    #     if tool_calls:
    #         # Step 3: call the function
    #         # Note: the JSON response may not always be valid; be sure to handle errors
    #         yield "Got some tools"

    #         available_functions = {
    #             "matchChunks": matchChunks,
    #         }  # only one function in this example, but you can have multiple
    #         messages.append(
    #             response_message
    #         )  # extend conversation with assistant's reply
    #         # Step 4: send the info for each function call and function response to the model
    #         for tool_call in tool_calls:
    #             yield "Calling function"
    #             function_name = tool_call.function.name
    #             function_to_call = available_functions[function_name]
    #             function_args = json.loads(tool_call.function.arguments)

    #             function_response = await function_to_call(**function_args)

    #             yield "Got response from function, calling 2nd endpoint"

    #             messages.append(
    #                 {
    #                     "tool_call_id": tool_call.id,
    #                     "role": "tool",
    #                     "name": function_name,
    #                     "content": function_response,
    #                 }
    #             )  # extend conversation with function response
    #         second_response = client.chat.completions.create(
    #             model="gpt-3.5-turbo-0125", messages=messages, stream=True
    #         )  # get a new response from the model where it can see the function response
    #         for chunk in second_response:
    #             if chunk.choices[0].delta.content is not None:
    #                 yield chunk.choices[0].delta.content
    # except Exception as e:
    #     print("Unable to generate ChatCompletion response")
    #     print(f"Exception: {e}")
    #     yield e
