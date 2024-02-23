import asyncio
import json
import threading


def streamSse(chunk, type: str = "text"):
    if type == "text":
        return f"data: {json.dumps({'event': 'text', 'value': chunk})}\n\n"

    x_chunk = json.dumps([{"text": chunk}])
    return f"data: {json.dumps({'event': 'data', 'value': x_chunk})}\n\n"


async def yield_in_thread(chunk, type="text"):
    print("Trying to stream,", chunk)
    loop = asyncio.get_running_loop()
    # Run the synchronous function in a separate thread without blocking
    # the asyncio event loop
    result = await loop.run_in_executor(None, streamSse, chunk, type)
    return result


# # # transforms the chunk into a stream part compatible with the vercel/ai
# def stream_chunk(chunk, type: str = "text"):
#     code = get_stream_part_code(type)
#     formatted_stream_part = f"{code}:{json.dumps(chunk, separators=(',', ':'))}\n"
#     return formatted_stream_part


# # given a type returns the code for the stream part
# def get_stream_part_code(stream_part_type: str) -> str:
#     stream_part_types = {
#         "text": "0",
#         "function_call": "1",
#         "data": "2",
#         "error": "3",
#         "assistant_message": "4",
#         "assistant_data_stream_part": "5",
#         "data_stream_part": "6",
#         "message_annotations_stream_part": "7",
#     }
#     return stream_part_types[stream_part_type]
