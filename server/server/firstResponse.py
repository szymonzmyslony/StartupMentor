from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from tools import matchChunks, sync_match_chunks, tools


system_message: ChatCompletionMessageParam = {
    "role": "system",
    "content": """You are a world-renowned tech startup mentor. Your job is to advise the founder on the startup they have. You should based your answers on first principles and give examples when possible. """,
}


def get_first_response(messages, context=""):
    new_messages = [system_message] + messages
    new_messages[-1] = {
        "role": "user",
        "content": f'Start up context is {context}, question is: {new_messages[-1]["content"]}',
    }

    client = OpenAI()
    response: ChatCompletion = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=new_messages,
        tools=tools,
        tool_choice="auto",
    )
    return response, new_messages
