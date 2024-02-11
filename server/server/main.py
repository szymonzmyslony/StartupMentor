# import openai
# import instructor

# from typing import Iterable, Literal
# from pydantic import BaseModel

# OPENAI_API_KEY = "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"

# import instructor
# from openai import OpenAI
# from typing import Iterable
# from pydantic import BaseModel

# client = instructor.patch(
#     OpenAI(api_key=OPENAI_API_KEY), mode=instructor.function_calls.Mode.JSON
# )


# class User(BaseModel):
# name: str
#     age: int


# users = client.chat.completions.create(
#     model="gpt-3.5-turbo-1106",
#     temperature=0.1,
#     response_model=Iterable[User],
#     stream=True,
#     messages=[
#         {
#             "role": "user",
#             "content": "Consider this data: Jason is 10 and John is 30.\
#                          Correctly segment it into entitites\
#                         Make sure the JSON is correct",
#         },
#     ],
# )
# for user in users:
#     print(user)
