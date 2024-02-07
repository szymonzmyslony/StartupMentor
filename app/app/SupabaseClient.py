# from supabase import create_client, Client
# from typing import List, Dict, Any, Tuple
# from pydantic import BaseModel
# from typing import Generic, TypeVar, List, Dict, Any, Optional
# from typing import Type
# from pydantic import BaseModel


# T = TypeVar("T")


# class SupabaseResult(BaseModel, Generic[T]):
#     data: Optional[T] = None
#     error: Optional[str] = None

#     def is_successful(self) -> bool:
#         """Check if the query was successful."""
#         return self.error is None


# # Data models for each function's return type
# class MatchChunkData(BaseModel):
#     id: int
#     document_id: int
#     title: str
#     content: str
#     similarity: float


# class MatchChunkWithinDocData(BaseModel):
#     id: int
#     title: str
#     content: str
#     similarity: float


# class MatchDocumentData(BaseModel):
#     id: int
#     title: str
#     summary: str
#     url: str
#     similarity: float


# M = TypeVar("M", bound=BaseModel)


# class SupabaseClient:
#     def __init__(self, url: str, key: str):
#         self.client: Client = create_client(url, key)

#     def call_function(
#         self,
#         function_name: str,
#         params: Dict[str, Optional[Any]],
#         response_model: Type[M],
#     ) -> SupabaseResult[List[M]]:
#         """Generic function to call Supabase functions, expecting a list response."""
#         try:
#             response = self.client.rpc(function_name, params).execute()

#             # Use parse_obj_as to parse the list of dictionaries into a list of model instances
#             data = [response_model.model_validate(item) for item in response.data]

#             return SupabaseResult[List[M]](data=data)

#         except Exception as e:
#             # Handle any exception by returning a SupabaseResult with the error
#             return SupabaseResult[List[M]](error=str(e))

#     # Example usage with a specific model
#     def match_chunk(
#         self,
#         query_embedding: List[float],
#         top_k: int = 10,
#         match_threshold: float = 0.0,
#     ) -> SupabaseResult[List[MatchChunkData]]:
#         """Call the match_chunk function."""
#         return self.call_function(
#             "match_chunk",
#             {
#                 "query_embedding": query_embedding,
#                 "top_k": top_k,
#                 "match_threshold": match_threshold,
#             },
#             MatchChunkData,  # Specify the Pydantic model directly
#         )

#     def match_chunk_within_document(
#         self,
#         document_id: int,
#         query_embedding: List[float],
#         top_k: int = 10,
#         match_threshold: float = 0.0,
#     ) -> SupabaseResult[List[MatchChunkWithinDocData]]:
#         """Call the match_chunk_within_document function."""
#         return self.call_function(
#             "match_chunk_within_document",
#             {
#                 "p_document_id": document_id,
#                 "query_embedding": query_embedding,
#                 "top_k": top_k,
#                 "match_threshold": match_threshold,
#             },
#             MatchChunkWithinDocData,
#         )

#     def match_document(
#         self,
#         query_embedding: List[float],
#         top_k: int = 10,
#         match_threshold: float = 0.0,
#     ) -> SupabaseResult[List[MatchDocumentData]]:
#         """Call the match_document function."""
#         return self.call_function(
#             "match_document",
#             {
#                 "query_embedding": query_embedding,
#                 "top_k": top_k,
#                 "match_threshold": match_threshold,
#             },
#             MatchDocumentData,
#         )

#     def get_child_chunks(self, document_id: int) -> List[Dict]:
#         try:
#             data = (
#                 self.client.table("chunks")
#                 .select("*")
#                 .eq("document_id", document_id)
#                 .execute()
#             )
#             return data.data
#         except Exception as e:
#             print(f"An error occurred: {e}")
#             return []

#     def get_parent_document(self, chunk_id: int) -> Dict:
#         try:
#             chunk = (
#                 self.client.table("chunks")
#                 .select("document_id")
#                 .eq("id", chunk_id)
#                 .single()
#                 .execute()
#                 .data
#             )
#             if chunk:
#                 document_id = chunk["document_id"]
#                 document = (
#                     self.client.table("documents")
#                     .select("*")
#                     .eq("id", document_id)
#                     .single()
#                     .execute()
#                     .data
#                 )
#                 return document
#             return {}
#         except Exception as e:
#             print(f"An error occurred: {e}")
#             return {}

#     def get_neighboring_chunks(self, chunk_id: int) -> Tuple[Dict, Dict]:
#         try:
#             current_chunk = (
#                 self.client.table("chunks")
#                 .select("*")
#                 .eq("id", chunk_id)
#                 .single()
#                 .execute()
#                 .data
#             )
#             if current_chunk:
#                 document_id = current_chunk["document_id"]
#                 order_index = current_chunk["order_index"]
#                 prev_chunk = (
#                     self.client.table("chunks")
#                     .select("*")
#                     .eq("document_id", document_id)
#                     .lt("order_index", order_index)
#                     .order("order_index", desc=True)
#                     .limit(1)
#                     .single()
#                     .execute()
#                     .data
#                 )
#                 next_chunk = (
#                     self.client.table("chunks")
#                     .select("*")
#                     .eq("document_id", document_id)
#                     .gt("order_index", order_index)
#                     .order("order_index")
#                     .limit(1)
#                     .single()
#                     .execute()
#                     .data
#                 )
#                 return prev_chunk, next_chunk
#             return None, None
#         except Exception as e:
#             print(f"An error occurred: {e}")
#             return None, None
