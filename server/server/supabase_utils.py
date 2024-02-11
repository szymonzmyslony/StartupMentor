import os
import json
from supabase import create_client, Client  # type: ignore


import json


def format_embeddings_as_pg_array(embeddings):
    # Convert each inner list (vector) to a JSON-like array string
    json_vectors = [
        '"' + json.dumps(embedding).replace('"', '\\"') + '"'
        for embedding in embeddings
    ]
    # Combine the JSON-like vectors into a single string representing a multidimensional array with curly braces
    array_string = "{" + ",".join(json_vectors) + "}"
    return array_string


class Supabase:
    def __init__(self):
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        self.client: Client = create_client(supabase_url, supabase_key)  # type: ignore

    async def match_chunks(self, query_embeddings: list[list[float]], top_k=5):
        try:
            response = self.client.rpc(
                "match_multiple_chunks",
                {
                    "query_embeddings": format_embeddings_as_pg_array(query_embeddings),
                    "top_k": top_k,
                },
            ).execute()
            data = response.data
            return data
        except Exception as error:
            print(f"Error in matchChunk: {error}")
            raise

    async def match_chunk(self, query_embedding, top_k=5, match_threshold=0.0):
        try:
            response = self.client.rpc(
                "match_chunk",
                {
                    "query_embedding": json.dumps(query_embedding),
                    "top_k": top_k,
                    "match_threshold": match_threshold,
                },
            ).execute()
            data = response.data
            return data
        except Exception as error:
            print(f"Error in matchChunk: {error}")
            raise

    async def match_chunk_within_document(
        self, document_id, query_embedding, top_k=10, match_threshold=0.0
    ):
        try:
            response = self.client.rpc(
                "match_chunk_within_document",
                {
                    "p_document_id": document_id,
                    "query_embedding": json.dumps(query_embedding),
                    "top_k": top_k,
                    "match_threshold": match_threshold,
                },
            ).execute()
            data = response.data
            return data
        except Exception as error:
            print(f"Error in matchChunkWithinDocument: {error}")
            raise

    async def match_document(self, query_embedding, top_k=10, match_threshold=0.0):
        try:
            response = self.client.rpc(
                "match_document",
                {
                    "query_embedding": json.dumps(query_embedding),
                    "top_k": top_k,
                    "match_threshold": match_threshold,
                },
            ).execute()
            data = response.data
            return data
        except Exception as error:
            print(f"Error in matchDocument: {error}")
            raise


# Instance of Supabase class
supabase = Supabase()


def get_supabase():
    return supabase
