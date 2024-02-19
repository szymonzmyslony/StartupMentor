from typing import Iterable, List
from pydantic import Field, BaseModel
from dotenv import load_dotenv
import instructor
from openai import OpenAI
import asyncio

from regex import F

load_dotenv()


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


client = instructor.patch(OpenAI(), mode=instructor.Mode.TOOLS)


def query_rewrite(user_query: str):

    response: FirstResponse = client.chat.completions.create(
        model="gpt-4-0125-preview",
        response_model=FirstResponse,
        max_retries=3,
        messages=[
            {
                "role": "system",
                "content": "You are a world renowned tech startup mentor. Your job is to contextualize founder question based on their background. Think step-by-step, breaking down complex questions to understand the core issues, and real world situations. Then ask any nesssary follow up questions to get a clear and concise answer as well as return the query plan.",
            },
            {"role": "user", "content": user_query},
        ],
    )
    return response
