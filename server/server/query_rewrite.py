from typing import Generator, Iterable, List
from pydantic import Field, BaseModel
from dotenv import load_dotenv
import instructor
from openai import OpenAI
import asyncio
from openai.types.chat import ChatCompletionMessageParam
from regex import F

load_dotenv()


class PotentialAnswer(BaseModel):
    """A potential answer to a follow-up question."""

    answer: str = Field(
        ...,
        description="Short and consise answer that the founder can provide to the follow-up question. Should be relvant to the context.",
    )


class Query(BaseModel):
    """Class representing a single question in a query plan."""

    topK: int = Field(..., description="How many chunks to retrieve for this question")
    question: str = Field(
        ...,
        description="Question asked using a question answering system",
    )


class QueryPlan(BaseModel):
    """Container class representing a tree of questions to ask a question answering system."""

    query_graph: List[Query] = Field(
        ...,
        description="The query graph representing the plan. Should be always at least 3 queries.",
    )


class FollowUp(BaseModel):
    question: str = Field(
        ...,
        description="Single follow up question probing founder for more context about their problem, expierence, or startup. Should be relvant to the oru",
    )
    potentialAnswers: List[str] = Field(
        ...,
        description="Potential answers to the follow-up question. Simple, short, and specific. No 'tech' ",
    )


class FirstResponse(BaseModel):
    """First response from the AI assistant."""

    result: QueryPlan | FollowUp


def get_first_answer(
    messages: List[ChatCompletionMessageParam],
    startup_context="empty",
    founder_context="empty",
) -> FirstResponse:
    client = instructor.patch(OpenAI())

    system_message: ChatCompletionMessageParam = {
        "role": "system",
        "content": "You are a world renowned tech startup mentor. You should understand whether you have enough context about the founder's background and their startup. If not, ask a follow-up question to get more context. Otherwise, rehash the question to fetch relevant data from the database.",
    }

    newMessages = [system_message] + messages

    newMessages[-1] = {
        "role": "user",
        "content": f'Start up context is {startup_context}, founder context is: {founder_context}. Founder says {newMessages[-1]["content"]}',
    }

    print(f"Submitting with newmessages", newMessages)

    result: FirstResponse = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=newMessages,
        response_model=FirstResponse,
        max_retries=3,
    )
    return result


def get_followUps(
    messages: List[ChatCompletionMessageParam],
) -> Generator[str, None, None]:
    client = instructor.patch(OpenAI())

    system_message: ChatCompletionMessageParam = {
        "role": "system",
        "content": "You are a world renowned tech startup mentor. Provide a list of potential answers to the follow-up question from the ai assistant. Those answers should ease the burder of the follow up question on the user. Each answer should be short and consise. At least 2, at max 5.",
    }
    newMessages = [system_message] + messages

    print("New messages are:", newMessages)

    choices: Iterable[PotentialAnswer] = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=newMessages,
        stream=True,
        response_model=Iterable[PotentialAnswer],
    )
    for choice in choices:
        yield choice.answer
