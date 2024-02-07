# from openai import OpenAI
# import os
# from dotenv import load_dotenv
# from supabase import create_client, Client

# from SupabaseClient import SupabaseClient

# load_dotenv()


# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# def get_embedding(text, model="text-embedding-3-small"):
#     response = client.embeddings.create(input=text, model=model, timeout=20)

#     return response.data


# supabase = SupabaseClient(url, key)


# def query_embedding(query):
#     embedding = get_embedding(query)

#     return embedding[0].embedding


# query = "How to do analitycs?"


# def get_instructions(query):
#     embedding = query_embedding(query)
#     chunks = supabase.match_chunk(query_embedding=embedding, top_k=3).data
#     if chunks:
#         retrieved_chunks = "\n".join(list(map(lambda x: x.content, chunks)))
#         print(len(retrieved_chunks))

#         return f"""

#     """
#     else:
#         return "no chunks found"


# def run_open_ai(user_message, model="gpt-3.5-turbo-0125"):
#     instructions = get_instructions(user_message)


# result = run_open_ai(query)
# print(result.choices[0].message.content)
