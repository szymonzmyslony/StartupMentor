from typing import AsyncGenerator, Generator, List
from openai import OpenAI
from tenacity import retry, sleep, stop_after_attempt, wait_random_exponential
from firstResponse import get_first_response
from query_rewrite import FollowUp, get_first_answer, get_followUps
from tools import matchChunks, sync_match_chunks, tools
from utils import streamSse
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionMessageParam,
)

GPT_MODEL = "gpt-3.5-turbo-0125"

client = OpenAI()


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def agent_request(
    messages, functions=None, model=GPT_MODEL
) -> Generator[str, None, None]:

    yield streamSse("Making first request", "data")

    startup_context = "Social commerce platform for farm2table based in London. Doing around 2k MRR and 15k of GMV."
    founder_context = ""

    response = get_first_answer(messages).result

    if isinstance(response, FollowUp):
        question = response.question
        yield streamSse(question, "text")
        yield streamSse("Follow up question", "data")
        return

    queries = list(map(lambda x: x.question, response.query_graph))

    print(
        "Calling with queries",
    )

    result = sync_match_chunks(queries)

    system_message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": "You are a world-renowned tech startup mentor. Your job is to advise the founder on the startup they have. You should based your answers on first principles and give examples when possible. Consider founder's background, particular industry, and the stage of the startup. Use only provided context from YC combinator provide a clear and concise answer.",
    }

    new_messages: List[ChatCompletionMessageParam] = [system_message] + messages

    new_messages[-1] = {
        "role": "user",
        "content": f'Start up context is {startup_context}, founder context is: {founder_context}. Founder question is: {new_messages[-1]["content"]}. YC combinator context is: {result}',
    }

    second_response = client.chat.completions.create(
        model="gpt-4-0125-preview", messages=new_messages, stream=True
    )  # get a new response from the model where it can see the function response
    for chunk in second_response:
        if chunk.choices[0].delta.content is not None:
            yield streamSse(chunk.choices[0].delta.content, "text")

    # if not tool_calls:
    #     yield streamSse("No tools", "data")
    #     yield streamSse(response_message.content, "text")
    #     new_messages = messages + [
    #         {
    #             "role": "assistant",
    #             "content": response_message.content,
    #         }
    #     ]
    #     print("New messages are:", new_messages)
    #     choices = get_followUps(new_messages)
    #     for c in choices:
    #         yield streamSse(c, "data")
    #     return
    # Step 2: check if the model wanted to call a function
    # if tool_calls:
    #     # Step 3: call the function
    #     # Note: the JSON response may not always be valid; be sure to handle errors
    #     yield streamSse("In toools ", "data")

    # available_functions = {
    #     "matchChunks": sync_match_chunks,
    # }  # only one function in this example, but you can have multiple
    # new_messages.append(
    #     response_message
    # )  # extend conversation with assistant's reply
    # # Step 4: send the info for each function call and function response to the model
    # for tool_call in tool_calls:
    #     yield streamSse("calling function", "data")
    #     function_name = tool_call.function.name
    #     function_to_call = available_functions[function_name]
    #     function_args = json.loads(tool_call.function.arguments)

    #     function_response = function_to_call(**function_args)

    #     yield streamSse("Callled function", "data")

    #     new_messages.append(
    #         {
    #             "tool_call_id": tool_call.id,
    #             "role": "tool",
    #             "name": function_name,
    #             "content": function_response,
    #         }
    #     )  # extend conversation with function response
    # print("Calling ifnal with", new_messages)
    # second_response = client.chat.completions.create(
    #     model="gpt-4-0125-preview", messages=new_messages, stream=True
    # )  # get a new response from the model where it can see the function response
    # for chunk in second_response:
    #     if chunk.choices[0].delta.content is not None:
    #         yield streamSse(chunk.choices[0].delta.content, "text")
