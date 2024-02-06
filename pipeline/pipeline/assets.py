import base64
from cgitb import text
from io import BytesIO
import json
import os
import random
import string
import re
from chunker.DocumentChunker import DocumentChunker
from cycler import concat
import requests
from dagster import (
    AssetExecutionContext,
    asset,
)  # import the `dagster` library
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List
import xml.etree.ElementTree as ET
import re
import numpy as np
from yaml import DocumentEndEvent

# from chunker.DocumentChunker import DocumentChunker
from pipeline.utils import extract_manual_docs
from .video_scraper import get_transcript

from .blog_scraper import extract_article_to_json, parse_md_into_string

from .data_utils import sort_yc_links


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
        # context.log.info(document["transcript"])
        title = document["title"]
        description = document["description"]
        # if content and len(content) > 10:
        #     content = parse_md_into_string(content)
        #     description = description + f"{content}"

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


def save_documents_to_files(combined_docs, base_dir="text_data"):
    """
    Saves each document from the combined list of documents to a separate file in the specified directory.

    Args:
    combined_docs (List[Dict]): The combined list of document dictionaries.
    base_dir (str): The base directory where the files will be saved.
    """
    # Ensure the base directory exists
    os.makedirs(base_dir, exist_ok=True)

    # Iterate over each document in the combined list
    for i, doc in enumerate(combined_docs):
        # Construct a unique filename for each document
        filename = f"doc_{i}.json"
        file_path = os.path.join(base_dir, filename)

        # Save the document's content to a JSON file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=4)

        # Optional: Log the path of the saved file for verification
        print(f"Document saved to: {file_path}")


# # Example usage


@asset
def docs_for_embeddings(
    context: AssetExecutionContext,
    combined_and_cleaned_video_docs,
    chunked_blog_docs,
) -> List:

    # Collect lengths of all text chunks
    text_chunk_lengths = [
        len(chunk[0]) for doc in chunked_blog_docs for chunk in doc["content"]
    ]
    context.log.info(f"Text Chunk Lengths: {text_chunk_lengths}")  # Debugging log

    # Calculate average length of text chunks using numpy and convert to Python float
    avg_text_length = float(np.average(text_chunk_lengths))
    max_text_length = float(np.max(text_chunk_lengths))
    min_text_length = float(np.min(text_chunk_lengths))

    # Collect lengths of all video chunks
    video_chunk_lengths = [
        len(chunk[0])
        for doc in combined_and_cleaned_video_docs
        for chunk in doc["transcript"]
    ]

    # Calculate average length of video chunks using numpy and convert to Python float
    avg_video_length = (
        float(np.average(video_chunk_lengths)) if video_chunk_lengths else 0.0
    )
    max_video_length = (
        float(np.max(video_chunk_lengths)) if video_chunk_lengths else 0.0
    )
    min_video_length = (
        float(np.min(video_chunk_lengths)) if video_chunk_lengths else 0.0
    )
    # Initialize variables to keep track of the maximum and minimum lengths and the corresponding chunks

    max_length = 0
    max_chunk = None
    min_length = float("inf")  # Set initial min_length to infinity for comparison
    min_chunk = None

    # Iterate over blog documents and their content chunks
    for doc in combined_and_cleaned_video_docs:
        for chunk in doc["transcript"]:
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

        # Proceed with the rest of the function as before

    combined_docs = combined_and_cleaned_video_docs + chunked_blog_docs

    # Add metadata for context
    context.add_output_metadata(
        metadata={
            "max_chunk": max_chunk,
            "min_chunk": min_chunk,
            "max_text_length": max_text_length,
            "min_text_length": min_text_length,
            "avg_text_chunk_length": avg_text_length,
            "max_video_length": max_video_length,
            "avg_video_chunk_length": avg_video_length,
            "min_video_length": min_video_length,
            "sample": combined_docs[:5],
            "sample1": combined_docs[-6:-1],
            "total_docs": len(combined_and_cleaned_video_docs) + len(chunked_blog_docs),
            "total_text_chunks": len(text_chunk_lengths),
            "total_video_chunks": len(video_chunk_lengths),
        }
    )
    save_documents_to_files(combined_docs)
    # Combine and return all documents
    return combined_and_cleaned_video_docs + chunked_blog_docs
