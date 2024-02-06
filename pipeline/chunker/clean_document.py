from typing import List, Optional, Tuple
from bs4 import BeautifulSoup

import markdown
from sqlalchemy import true
import re

MAX_LENGTH = 2000


def find_split_point(s, limit):
    # Search for punctuation marks near the limit
    for punct in (".", "?", "!"):
        split_point = s.rfind(punct, 0, limit + 1)  # Include punctuation in the split
        if split_point != -1:
            return split_point + 1  # Include the punctuation mark in the first part
    # If no suitable punctuation is found, fallback to splitting at the limit
    return limit


def split_text(text, max_length=MAX_LENGTH):
    # Split the text into chunks that are less than or equal to max_length
    parts = []
    while len(text) > max_length:
        split_at = find_split_point(text, max_length)
        parts.append(text[:split_at].strip())
        text = text[split_at:].strip()  # Remove leading whitespace from the next part
    parts.append(text)  # Add the last chunk
    return parts


# Integrate the modified split_text in the parse_md_to_semantic_sections function
def parse_md_to_semantic_sections(md_text, max_section_length=3000):
    sections = []
    current_text = []
    current_title = "Introduction"

    header_pattern = re.compile(r"^\s*(#+)\s*(.*)", re.MULTILINE)

    for line in md_text.split("\n"):
        header_match = header_pattern.match(line)
        if header_match:
            if current_text:
                full_text = clean_single_paragraph("\n".join(current_text))
                if len(full_text) > max_section_length:
                    text_parts = split_text(full_text, max_section_length)
                    for i, part in enumerate(text_parts, 1):
                        sections.append(
                            {
                                "title": f"{current_title} (Part {i})",
                                "text": part,
                            }
                        )
                else:
                    sections.append(
                        {
                            "title": current_title,
                            "text": full_text,
                        }
                    )
                current_text = []
            current_title = header_match.group(2).strip()
        else:
            current_text.append(line)

    if current_text:
        full_text = clean_single_paragraph("\n".join(current_text))
        if len(full_text) > max_section_length:
            text_parts = split_text(full_text, max_section_length)
            for i, part in enumerate(text_parts, 1):
                sections.append(
                    {
                        "title": f"{current_title} (Part {i})",
                        "text": part,
                    }
                )
        else:
            sections.append(
                {
                    "title": current_title,
                    "text": full_text,
                }
            )

    return sections


def clean_single_paragraph(paragraph):

    def parse_md_to_text(md_text):
        """Converts markdown text to plain text, preserving contractions."""
        # Convert Markdown to HTML
        html = markdown.markdown(md_text)
        # Use 'get_text' with a space as the separator to preserve contractions
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        return text

    def replace_non_ascii_characters_with_space(text):
        """Replaces non-ASCII characters in the text with a single space."""
        allowed_chars = set("`'‘’.-?!\"“”")

        return "".join(
            char if char.isascii() or char in allowed_chars else " " for char in text
        )

    text = parse_md_to_text(paragraph)
    text = replace_non_ascii_characters_with_space(text)
    return text


def process_document(text: str):
    sections = parse_md_to_semantic_sections(text)
    # print("Definetely have more than 2 sections", len(sections) > 2)
    if len(sections) > 3:
        return sections, True

    result = splitByNewLines(text)

    return result, False


def splitByNewLines(document):
    def split_long_paragraph(section, max_length=MAX_LENGTH):

        if len(section) <= max_length:
            return [section]
        else:
            # Find a suitable split point based on punctuation
            split_point = find_split_point(section, max_length)
            # Split the section and recursively process the remaining part
            return [section[:split_point]] + split_long_paragraph(
                section[split_point:], max_length
            )

    if document.count("\n\n") > 2:
        sections = document.split("\n\n")
    else:
        sections = document.split("\n")

    # Assuming clean_single_paragraph is defined elsewhere
    cleaned_sections = map(clean_single_paragraph, sections)

    # Split sections further if they exceed the max length
    split_sections = []
    for section in cleaned_sections:
        split_sections.extend(split_long_paragraph(section))

    # Filter out empty sections
    filtered = list(filter(lambda x: len(x) > 0, split_sections))

    # for section in filtered:
    #     print(len(section))

    # Wrap each section in a dictionary
    final = [{"title": None, "text": section} for section in filtered]
    return final
