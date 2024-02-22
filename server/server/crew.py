import asyncio
from asyncore import loop
from concurrent.futures import ThreadPoolExecutor
import json
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential
from openai.types.chat import ChatCompletion
from tools import matchChunks, sync_match_chunks, tools


GPT_MODEL = "gpt-3.5-turbo-0125"

client = OpenAI()


def run_async_in_thread(func, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    future = asyncio.ensure_future(func(**kwargs))
    return loop.run_until_complete(future)


def run_in_thread(func, *args, **kwargs):
    # Directly call the synchronous function with provided arguments.
    return func(*args, **kwargs)


def get_completion_sync(model, messages, tools, tool_choice):
    with ThreadPoolExecutor() as executor:
        future = executor.submit(
            run_in_thread,
            client.chat.completions.create,
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return future.result()


def matchChunkSync(**function_args):
    with ThreadPoolExecutor() as executor:
        future = executor.submit(
            run_async_in_thread,
            matchChunks,
            queries=function_args.get("queries"),
            topK=function_args.get("topK"),
        )
        return future.result()


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def agent_request(messages, functions=None, model=GPT_MODEL):
    try:
        yield "Making first request"

        response: ChatCompletion = get_completion_sync(
            model="gpt-3.5-turbo-0125",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        response_message = response.choices[0].message
        yield "Received first message"

        tool_calls = response_message.tool_calls

        # Step 2: check if the model wanted to call a function
        if tool_calls:
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            yield "Got some tools"

            available_functions = {
                "matchChunks": matchChunkSync,
            }  # only one function in this example, but you can have multiple
            messages.append(
                response_message
            )  # extend conversation with assistant's reply
            # Step 4: send the info for each function call and function response to the model
            for tool_call in tool_calls:
                yield "Calling function"
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)

                function_response = function_to_call(**function_args)

                yield "Got response from function, calling 2nd endpoint"

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )  # extend conversation with function response
            second_response = client.chat.completions.create(
                model="gpt-3.5-turbo-0125", messages=messages, stream=True
            )  # get a new response from the model where it can see the function response
            for chunk in second_response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        yield e
