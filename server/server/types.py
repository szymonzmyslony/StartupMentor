from typing import Any, Dict, List, Optional, Union, TypedDict

# # Define the JSON type recursively
# JSONType = Union[str, int, float, bool, None, Dict[str, Any], List["JSONType"]]


class ChunkRow(TypedDict):
    content: str
    document_id: int
    embedding: Optional[str]
    id: int
    order_index: Optional[int]
    title: Optional[str]


# class ChunkRow(TypedDict):
#     content: Optional[str]
#     document_id: int
#     embedding: Optional[str]
#     id: int
#     order_index: Optional[int]
#     title: Optional[str]


# class ChunkInsert(TypedDict, total=False):
#     content: Optional[str]
#     document_id: int
#     embedding: Optional[str]
#     id: Optional[int]
#     order_index: Optional[int]
#     title: Optional[str]


# class ChunkUpdate(TypedDict, total=False):
#     content: Optional[str]
#     document_id: Optional[int]
#     embedding: Optional[str]
#     id: Optional[int]
#     order_index: Optional[int]
#     title: Optional[str]


# class DocumentRow(TypedDict):
#     embedding: Optional[str]
#     id: int
#     meta: Optional[JSONType]
#     summary: Optional[str]
#     title: Optional[str]
#     url: Optional[str]


# class DocumentInsert(TypedDict, total=False):
#     embedding: Optional[str]
#     id: Optional[int]
#     meta: Optional[JSONType]
#     summary: Optional[str]
#     title: Optional[str]
#     url: Optional[str]


# class DocumentUpdate(TypedDict, total=False):
#     embedding: Optional[str]
#     id: Optional[int]
#     meta: Optional[JSONType]
#     summary: Optional[str]
#     title: Optional[str]
#     url: Optional[str]


# # Define other types as needed following the pattern above

# # Example usage of the defined types
# chunk: ChunkRow = {
#     "content": "Example content",
#     "document_id": 1,
#     "embedding": "Some embedding",
#     "id": 123,
#     "order_index": 1,
#     "title": "Example Title",
# }

# document: DocumentRow = {
#     "embedding": "Some embedding",
#     "id": 456,
#     "meta": {"key": "value"},  # Example JSON
#     "summary": "Example Summary",
#     "title": "Example Document Title",
#     "url": "http://example.com",
# }
