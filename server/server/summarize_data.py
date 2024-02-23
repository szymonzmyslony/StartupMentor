from openai import OpenAI


def summarize_startup_context(messages, context):
    """
    Summarize the startup context.


    """

    system_message = {
        "role": "system",
        "content": """Extract key learnings and advise startup founder how to best move forward and think about their problems. You should base your answer on the context below and understanding founder's startup as well as the problems they are facing.
        Context:{context}""",
    }

    new_messages = [system_message] + messages
    client = OpenAI()
    second_response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125", messages=new_messages, stream=True
    )  # get a new response from the model where it can see the function response
    for chunk in second_response:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content
