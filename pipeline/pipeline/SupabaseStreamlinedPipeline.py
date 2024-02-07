# import os
# from sre_compile import isstring
# from typing import Dict, Any

# from supabase import create_client, Client
# from chunker.embeddings import batch_paragraphs, get_embedding
# import time
# import base64
# import json


# class SupabaseDocumentInserter:
#     def __init__(self, url, key):
#         self.supabase: Client = create_client(url, key)

#     def get_embeddings_in_batches(self, texts, logger=print):
#         batches = batch_paragraphs(texts, logger)  # Use your existing batching function
#         all_embeddings = []
#         for batch in batches:
#             batch_embeddings = [x.embedding for x in get_embedding(batch)]
#             all_embeddings.extend(batch_embeddings)
#         return all_embeddings

#     def encode_embedding(self, embedding):
#         return embedding
#         # Assuming embedding is a numpy array, adjust if it's different.
#         # Convert it to bytes, then encode it to a base64 string for JSON serialization.
#         # return base64.b64encode(embedding.tobytes()).decode("utf-8")

#     def insert_doc_with_chunks(self, doc, logger=print):
#         # Prepare document embedding
#         title = doc["title"]
#         description = doc["description"]
#         document_text = (
#             f"Title: {title}, Description: {description}"
#             if title and description
#             else " ".join(doc[0] for doc in doc["content"])
#         )
#         document_embedding = self.get_embeddings_in_batches([document_text], logger)[0]
#         encoded_document_embedding = self.encode_embedding(document_embedding)

#         # Prepare chunks embeddings
#         content = doc["content"]
#         texts = [item[0] for item in content]
#         titles = [item[1] for item in content]
#         new_texts = list(map(lambda x: x.replace("\n", " "), texts))
#         new_titles = list(
#             map(lambda x: x.replace("\n", " ") if isstring(x) else "", titles)
#         )
#         new_content = list(zip(new_texts, new_titles))
#         chunk_embeddings = self.get_embeddings_in_batches(new_texts, logger)

#         # Prepare chunks data with encoded embeddings
#         chunks_data = [
#             {
#                 "title": new_titles[i],
#                 "content": new_texts[i],
#                 "order_index": i,
#                 "embedding": self.encode_embedding(chunk_embeddings[i]),
#             }
#             for i in range(len(new_texts))
#         ]

#         # Prepare the RPC payload
#         rpc_payload = {
#             "doc_title": title,
#             "doc_summary": description,
#             "doc_url": doc["url"],
#             "doc_meta": {},
#             "doc_embedding": encoded_document_embedding,
#             "chunk_data": json.dumps(chunks_data),
#         }

#         # Call the PostgreSQL function via RPC
#         response = self.supabase.rpc("insert_document_with_chunks", rpc_payload)
#         result = response.execute()
#         print(result)

#         # Check for errors in the response
#         # if 'error' in result:
#         #     logger(f"Failed to insert document and chunks: {result['error']['message']}")
#         #     return None
#         # elif result !=


# # Example usage:
# # inserter = SupabaseDocumentInserter('your_supabase_url', 'your_supabase_key')
# # inserter.insert_doc_with_chunks(document_data, print)
