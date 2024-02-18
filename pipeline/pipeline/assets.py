import json
import os
import re

from instructor import Maybe
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from chunker.DocumentChunker import DocumentChunker
from pipeline.SupabasePipeline import SupabaseDocumentInserter
import requests
from dagster import (
    AssetExecutionContext,
    asset,
)  # import the `dagster` library
import pandas as pd
from typing import Dict, List
import xml.etree.ElementTree as ET
import re
import numpy as np
from yaml import DocumentEndEvent
from .file_utils import save_documents_to_files
from dotenv import load_dotenv

# from chunker.DocumentChunker import DocumentChunker
from pipeline.utils import extract_manual_docs
from .video_scraper import get_transcript
from .blog_scraper import extract_article_to_json, parse_md_into_string
from .data_utils import sort_yc_links

load_dotenv()


@asset
def manual_articles(context: AssetExecutionContext) -> List:
    urls = []
    base_url = "https://www.ycombinator.com/library/"
    directory = "./yc_manual"
    for filename in os.listdir(directory):
        # Check if the file is a JSON file
        if filename.endswith(".json"):
            # Construct the full file path
            filepath = os.path.join(directory, filename)

            # Open and read the JSON file
            with open(filepath, "r") as file:
                try:
                    # Parse the JSON content
                    data = json.load(file)

                    # Extract the 'url' field
                    url = data.get(
                        "url"
                    )  # Use .get to avoid KeyError if 'url' field is missing

                    # Do something with the url, e.g., print it
                    if url:
                        merged_url = base_url + url
                        urls.append(merged_url)

                except json.JSONDecodeError:
                    print(f"Error decoding JSON from {filename}")
    context.add_output_metadata(metadata={"length": len(urls), "urls": urls})
    return urls


@asset
def library_links(context: AssetExecutionContext, manual_articles) -> List:
    sitemap_url = "https://www.ycombinator.com/library/sitemap.xml"
    response = requests.get(sitemap_url)
    sitemap_content = response.text
    root = ET.fromstring(sitemap_content)

    # Extract URLs
    urls = [
        loc.text
        for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        if loc.text
        not in manual_articles  # This condition filters out URLs present in manual_urls
    ]

    # Filter URLs
    context.add_output_metadata(
        metadata={"num_records": len(urls), "preview": urls[:5]}
    )

    return urls


@asset
def filtered_links(context: AssetExecutionContext, library_links: List) -> List:
    pattern = r"^https://www\.ycombinator\.com/library/[A-Za-z0-9\-]+$"

    filtered = [url for url in library_links if re.match(pattern, url)]

    context.add_output_metadata(
        metadata={"num_records": len(filtered), "preview": filtered[:5]}
    )

    return filtered


@asset
def sorted_links(context: AssetExecutionContext, filtered_links) -> Dict:
    youtube_urls, spotify_urls, text_urls = sort_yc_links(filtered_links)

    context.add_output_metadata(
        metadata={
            "spotify_links": len(spotify_urls),
            "text_urls": len(text_urls),
            "youtube_link": len(youtube_urls),
            "text_example": text_urls[:5],
            "youtube_example": youtube_urls[:5],
        }
    )

    return {
        "links_to_videos": youtube_urls,
        "links_to_text": text_urls,
        "links_to_spotify": spotify_urls,
    }


@asset
def fetched_blog_content(context: AssetExecutionContext, sorted_links) -> List:
    text_urls = sorted_links["links_to_text"]
    result = []
    for url in text_urls:
        content = extract_article_to_json(url)
        result.append(content)
    # save_documents_to_files(result)
    context.add_output_metadata(metadata={"length": len(result), "sample": result[:5]})
    return result


@asset
def video_content(context: AssetExecutionContext, sorted_links) -> List:
    video_urls = sorted_links["links_to_videos"]
    result = []
    for url in video_urls:
        context.log.info(url)

        content = extract_article_to_json(url, parse_yt_id=True)
        if content:
            result.append(content)

    context.add_output_metadata(metadata={"length": len(result), "sample": result[:5]})
    return result


@asset
def complete_video_content(context: AssetExecutionContext, video_content) -> Dict:
    result = []
    errors = []
    for asset in video_content:
        title = asset["title"]
        content = asset["content"]
        url = asset["url"]
        description = asset["description"]
        transcript = asset["transcript"]
        youtube_id = asset["youtube_id"]
        fetching_youtube = False
        if not transcript:
            if not isinstance(youtube_id, str):
                errors.append(
                    {
                        "title": title,
                        "content": content,
                        "description": description,
                        "transcript": transcript,
                        "url": url,
                        "youtube_id": youtube_id,
                        "error": "id is not string",
                    }
                )
                continue

            try:
                fetching_youtube = True
                transcript = get_transcript(youtube_id)
                # transcript = map(lambda x: x["text"], fetched_transcript)
            except (
                Exception
            ) as e:  # Catching a generic exception, consider using a more specific one if possible
                errors.append(
                    {
                        "title": title,
                        "content": content,
                        "description": description,
                        "transcript": transcript,
                        "url": url,
                        "youtube_id": youtube_id,
                        "error": str(e),
                    }
                )
                continue  # Skip the rest of the loop and move to the next iteration if an error occurs

        new_asset = {
            "youtube_id": youtube_id,
            "title": title,
            "content": content,
            "url": url,
            "description": description,
            "transcript": transcript,
            "fetching_transcript": fetching_youtube,
        }
        result.append(new_asset)

    context.add_output_metadata(
        metadata={"length": len(result), "sample": result[:5], "erros": errors}
    )
    return {"result": result, "errors": errors}


@asset
def chunked_blog_docs(
    context: AssetExecutionContext,
    fetched_blog_content,
) -> List:
    manual_docs = extract_manual_docs("./yc_manual")

    def chunk_document(document):
        context.log.info(document["url"])
        context.log.info(document["content"])
        content = document["content"]
        title = document["title"]
        description = document["description"]

        chunker = DocumentChunker(content, title, description, context.log.info)

        chunks, title = chunker.chunk_document()
        return list(zip(chunks, title))

    combined = fetched_blog_content + manual_docs
    cleaned_documents = [
        {**blog, "content": chunk_document(blog)}
        for blog in combined
        if blog["content"] and len(blog["content"]) > 10
    ]

    chunk_sizes = list(
        map(
            lambda x: {"url": x["url"], "chunks_length": len(x["content"])},
            cleaned_documents,
        )
    )

    context.add_output_metadata(
        metadata={
            "length": len(cleaned_documents),
            "sample": cleaned_documents[:5],
            "chunk_sizes": chunk_sizes,
        }
    )
    save_documents_to_files(cleaned_documents, "./chunked_data")
    return cleaned_documents


@asset
def combined_and_cleaned_video_docs(
    context: AssetExecutionContext, complete_video_content
) -> List:
    def chunk_document(document):
        context.log.info(document["url"])
        title = document["title"]
        description = document["description"]

        transcript = document["transcript"]
        transcript_chunker = DocumentChunker(
            transcript,
            title,
            description,
            context.log.info,
        )

        chunks, title = transcript_chunker.chunk_document()
        return list(zip(chunks, title))

    complete_video_content = complete_video_content["result"]
    cleaned_documents = [
        {**video, "transcript": transcript}
        for video in complete_video_content
        if video["transcript"] and len(video["transcript"]) > 10
        for transcript in [
            chunk_document(video)
        ]  # Unpacks the tuple into content and transcript
    ]

    context.add_output_metadata(
        metadata={
            "length": len(cleaned_documents),
            "sample": cleaned_documents[100:105],
        }
    )

    cleaned_documents_with_parsed_content = list(
        map(
            lambda x: {
                **x,
                "content": (
                    parse_md_into_string(x["content"])
                    if isinstance(x["content"], str)
                    else x["content"]
                ),
            },
            cleaned_documents,
        )
    )
    return cleaned_documents_with_parsed_content


# import json
# import os


# # Example usage


@asset
def docs_for_embeddings(
    context: AssetExecutionContext,
    combined_and_cleaned_video_docs,
    chunked_blog_docs,
) -> List:

    # Collect lengths of all text chunks

    combined_docs = (
        list(
            map(
                lambda x: {
                    **{k: v for k, v in x.items() if k != "transcript"},
                    "content": x["transcript"],
                },
                combined_and_cleaned_video_docs,
            )
        )
        + chunked_blog_docs
    )
    combined_chunk_lengths = [
        len(chunk[0]) for doc in combined_docs for chunk in doc["content"]
    ]

    # Calculate average length of text chunks using numpy and convert to Python float
    avg_combined_length = float(np.average(combined_chunk_lengths))
    max_combined_length = float(np.max(combined_chunk_lengths))
    min_combined_length = float(np.min(combined_chunk_lengths))

    max_length = 0
    max_chunk = None
    min_length = float("inf")  # Set initial min_length to infinity for comparison
    min_chunk = None

    # # Iterate over blog documents and their content chunks
    for doc in combined_docs:
        for chunk in doc["content"]:
            # Calculate the length of the current chunk
            chunk_length = len(chunk[0]) if chunk and chunk[0] else 0

            # Update max_length and max_chunk if the current chunk is longer than max_length
            if chunk_length > max_length:
                max_length = chunk_length
                max_chunk = chunk[0]  # Store the content of the chunk

            # Update min_length and min_chunk if the current chunk is shorter than min_length and not empty
            if 0 < chunk_length < min_length:
                min_length = chunk_length
                min_chunk = chunk[0]  # Store the content of the chunk

    # Log the maximum and minimum lengths and the corresponding chunks for debugging
    context.log.info(f"Maximum Text Chunk Length: {max_length}")
    if max_chunk:
        context.log.info(
            f"Text Chunk with Maximum Length: {max_chunk[:100]}..."
        )  # Show only the first 100 characters for brevity

    context.log.info(f"Minimum Text Chunk Length: {min_length}")
    if min_chunk:
        context.log.info(
            f"Text Chunk with Minimum Length: {min_chunk[:100]}..."
        )  # Show only the first 100 characters for brevity

    #     # Proceed with the rest of the function as before

    # Add metadata for context
    context.add_output_metadata(
        metadata={
            "max_chunk": max_chunk,
            "min_chunk": min_chunk,
            "max_text_length": max_combined_length,
            "min_text_length": min_combined_length,
            "avg_text_chunk_length": avg_combined_length,
            "sample": combined_docs[:5],
            "sample1": combined_docs[-6:-1],
            "keys": list(combined_docs[0].keys()),
            "total_docs": len(combined_docs),
            # "total_video_chunks": len(video_chunk_lengths),
        }
    )
    save_documents_to_files(combined_docs, "./data")
    # Combine and return all documents
    return combined_docs


url: str = "https://tqgqncfjpjpmsqstegnc.supabase.co"
key: str = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRxZ3FuY2ZqcGpwbXNxc3RlZ25jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDcxNjE1MDYsImV4cCI6MjAyMjczNzUwNn0.J3PDrkKEiZOW02W8yZ2-8V_Hyqyh0p3rxguo0SyYkYw"
)


@asset
def summarize_chunks(context: AssetExecutionContext, docs_for_embeddings) -> List:
    def generate_summary(title, text: str):

        class Summary(BaseModel):
            """Class representing a summary of a doc"""

            key_question: list[str] = Field(
                ...,
                description="Key questions that the document chunk answers. At least 1, max 3",
            )
            key_points: list[str] = Field(
                ...,
                description="Key points for the document chunk. Should include general advice and examples.",
            )

        client = instructor.patch(OpenAI())

        prompt = (
            "Summarize the key points and generate questions that this advice answers. "
            "Use simple language and be concise. Avoid using any personal names, including those present in the document."
        )
        message_content = (
            f"Chunk content: {text}"
            if title == ""
            else f"Title: {title}, Chunk content: {text}"
        )

        return client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_model=Summary,
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": message_content,
                },
            ],
        )

    summarized_docs = []  # Initialize a list to hold the documents with their summaries

    for doc in docs_for_embeddings:
        # Assuming 'doc' is a dictionary that may contain 'title' and 'description' keys
        title = doc.get("title") if isinstance(doc.get("title"), str) else ""
        description = (
            doc.get("description") if isinstance(doc.get("description"), str) else ""
        )
        document_title = f"{title}, {description}".strip(", ")

        content = doc["content"]

        summaries = (
            []
        )  # Initialize a list to hold summaries for each chunk of the document
        for chunk in content:
            text = chunk[0].replace("\n", " ")  # Prepare the chunk text
            summary = generate_summary(document_title, text)
            summaries.append(
                {
                    "key_points": summary.key_points,
                    "key_questions": summary.key_question,
                }
            )

        # Append the original document with its summaries to the summarized_docs list
        summarized_doc = {
            **doc,  # Include all original document data
            "summaries": summaries,  # Add the new summaries
        }
        summarized_docs.append(summarized_doc)
    context.add_output_metadata(
        metadata={"length": len(summarized_docs), "sample": summarized_docs[:5]}
    )
    return summarized_docs


@asset
def summarize_docs(context: AssetExecutionContext, summarize_chunks) -> List:
    errors = []
    summarized_docs = []  # Initialize a list to hold the documents with their summaries

    def generate_summary(title: str, key_points: str, key_questions: str):

        class Summary(BaseModel):
            """Class representing a summary of a doc"""

            key_questions: list[str] = Field(
                ...,
                description="Key questions that the document. At least 1, max 5",
            )
            key_points: list[str] = Field(
                ...,
                description="Key points for the document. Should include general advice and examples.",
            )

        client = instructor.patch(OpenAI())

        prompt = (
            "You will receive key points and questions for multiple chunks in a single document"
            "Generate simple and concise summary and questions for the whole document. Include real-world examples and first principles"
            "Use simple language and be concise. Avoid using any personal names, including those present in the document."
        )
        key_prompts = (
            f"Chunks key points: {key_points} Chunk questions: {key_questions}"
        )
        message_content = (
            key_prompts if title == "" else f"Title: {title}, {key_prompts}"
        )

        return client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_model=Summary,
            max_retries=3,
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": message_content,
                },
            ],
        )

    for doc in summarize_chunks:
        # Assuming 'doc' is a dictionary that may contain 'title' and 'description' keys
        title = doc.get("title") if isinstance(doc.get("title"), str) else ""
        description = (
            doc.get("description") if isinstance(doc.get("description"), str) else ""
        )
        document_title = f"{title}, {description}".strip(", ")

        summaries = doc["summaries"]

        key_questions = [("\n").join(summary["key_questions"]) for summary in summaries]
        key_points = [("\n").join(summary["key_points"]) for summary in summaries]

        key_questions = ("\n").join(key_questions)
        key_points = ("\n").join(key_points)

        generated = generate_summary(document_title, key_points, key_questions)

        content = doc["content"]

        zipped_data = [
            [chunk, original_title, summary["key_points"], summary["key_questions"]]
            for (chunk, original_title), summary in zip(content, summaries)
        ]

        # Append the original document with its summaries to the summarized_docs list
        summarized_doc = {
            **doc,  # Include all original document data
            "key_points": generated.key_points,  # Add the new summaries
            "content": zipped_data,
            "key_questions": generated.key_questions,
        }

        summarized_docs.append(summarized_doc)
    context.add_output_metadata(
        metadata={"length": len(summarized_docs), "sample": summarized_docs[:1]}
    )
    return summarized_docs


@asset
def embed_and_save_docs(context: AssetExecutionContext, summarize_docs) -> List:
    inserter = SupabaseDocumentInserter(url, key)
    errors = []

    for index, doc in enumerate(summarize_docs):
        inserter.insert_doc_with_chunks(doc, context.log.info)

    context.add_output_metadata(metadata={"errors": errors})
    return errors
