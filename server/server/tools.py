import asyncio
from openai.types.chat import ChatCompletionToolParam
from typing import Iterable, List
from embeddigs import embedding_request
from supabase_utils import get_supabase


tools: Iterable[ChatCompletionToolParam] = [
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


def process_single_chunks_retieval(query, chunks):
    content = "\n".join([chunk["content"] for chunk in chunks])
    urls: List[str] = [chunk["url"] for chunk in chunks]
    content = f'Content for query "{query}":\n{content}\n'
    return {"content": content, "sources": urls}


async def matchChunks(queries: List[str], topK: int):
    supabase = get_supabase()
    query_embeddings = list(map(lambda x: x.embedding, embedding_request(queries)))

    result = await supabase.match_chunks(query_embeddings, top_k=2)

    mapped_result = [
        process_single_chunks_retieval(queries[i], result[i]["chunk_details"])
        for i in range(len(queries))
    ]
    print("mapped result", len(mapped_result))
    content = "\n".join([x["content"] for x in mapped_result])
    urls: list[str] = [source for x in mapped_result for source in x["sources"]]

    print("retrieved urls", list(set(urls)))
    return content


def sync_match_chunks(queries: List[str], topK: int):
    # This function will run the asynchronous matchChunks function synchronously
    return asyncio.run(matchChunks(queries, topK))
