import os
from sre_compile import isstring
from chunker.clean_document import split_text
from chunker.openai_utils import num_tokens_from_string

from supabase import create_client, Client
from chunker.embeddings import batch_paragraphs, get_embedding
import time


class SupabaseDocumentInserter:
    def __init__(self, url, key):
        self.supabase: Client = create_client(url, key)

    def insert_chunks_with_retry(
        self,
        document_id,
        chunks,
        logger=print,
        max_retries=3,
        delay=2,
    ):
        for attempt in range(max_retries):
            try:
                self.batch_insert_chunks(document_id, chunks, logger)
                break  # Break the loop if insertion is successful
            except TimeoutError as e:
                logger(
                    f"Write timeout on attempt {attempt+1}. Retrying in {delay} seconds..."
                )
                time.sleep(delay)  # Wait for a bit before retrying
            except Exception as e:
                logger(f"An unexpected error occurred: {e}")
                break  # Exit on other types of exceptions

    def get_embeddings_in_batches(self, texts, logger=print):
        print(f"Texts are {len(texts)}")
        batches = batch_paragraphs(texts, logger)  # Use your existing batching function
        all_embeddings = []
        for batch in batches:
            batch_embeddings = [x.embedding for x in get_embedding(batch)]
            all_embeddings.extend(batch_embeddings)
        return all_embeddings

    def insert_document(self, title, summary, url, meta, embedding, logger=print):
        data = (
            self.supabase.table("documents")
            .insert(
                {
                    "title": title,
                    "summary": summary,
                    "url": url,
                    "meta": meta,
                    "embedding": embedding,
                }
            )
            .execute()
        )
        return data

    def insert_document_with_embedding(self, doc, logger=print):
        title = doc["title"]
        description = doc["description"]
        document_text = ""
        if title:
            document_text += f"Title: {title}"
        if description:
            document_text += f", Description: {description}"
        if not document_text:
            document_text = " ".join(doc[0] for doc in doc["content"])
            document_text = document_text.replace("\n", " ")
            if num_tokens_from_string(document_text) > 8000:
                document_text = split_text(document_text)
        if isstring(document_text):
            document_text = [document_text]
        document_embedding = self.get_embeddings_in_batches(document_text, logger)[0]

        document_data = self.insert_document(
            title=title,
            summary=description,
            url=doc["url"],
            meta={},
            embedding=document_embedding,
            logger=logger,
        )

        document_id = document_data.data[0]["id"]
        return document_id

    def batch_insert_chunks(self, document_id, chunks, logger=print):
        chunk_texts = [chunk[0] for chunk in chunks]
        chunk_embeddings = self.get_embeddings_in_batches(chunk_texts, logger)

        chunks_data = []

        for index, item in enumerate(chunks):
            text = item[0]
            title = item[1]
            chunk_embedding = (
                chunk_embeddings[index] if index < len(chunk_embeddings) else None
            )
            if chunk_embedding is None:
                logger(f"No embedding for chunk {index}, skipping.")
                continue

            chunks_data.append(
                {
                    "document_id": document_id,
                    "title": title,
                    "content": text,
                    "order_index": index,
                    "embedding": chunk_embedding,
                }
            )

        if chunks_data:
            try:
                self.supabase.table("chunks").insert(chunks_data).execute()
            except (
                Exception
            ) as e:  # Replace Exception with the specific exception for timeouts if available
                logger(f"Error during chunk insertion: {e}")
                raise TimeoutError("Write timeout occurred during chunk insertion")

    def insert_doc_with_chunks(self, doc, logger=print):
        new_title = doc["title"].replace("\n", " ") if doc["title"] else ""
        new_description = (
            doc["description"].replace("\n", " ") if doc["description"] else ""
        )
        content = doc["content"]
        texts = [item[0] for item in content]
        titles = [item[1] for item in content]
        new_texts = list(map(lambda x: x.replace("\n", " "), texts))
        new_titles = list(
            map(lambda x: x.replace("\n", " ") if isstring(x) else "", titles)
        )
        new_content = list(zip(new_texts, new_titles))
        new_doc = {
            **doc,
            "title": new_title,
            "description": new_description,
            "content": new_content,
        }
        print(len(new_content))
        document_id = self.insert_document_with_embedding(new_doc, logger)
        if not document_id:
            logger("Failed to insert document, skipping chunks.")
            return
        self.insert_chunks_with_retry(document_id, new_content, logger=logger)


# Example usage:
