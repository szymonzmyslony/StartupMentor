# from typing import List
# from bs4 import BeautifulSoup
# from chunker.clean_document import clean_single_paragraph
# import markdown


# import json

# from pydantic import BaseModel


# class SemanticSection:
#     title: str
#     text: str

#     def __init__(self, **data):
#         super().__init__(**data)

#     def clean(self):
#         """Cleans the section's text by removing Markdown and replacing non-ASCII characters."""
#         self.text = clean_single_paragraph(self.text)
#         return self

#     def to_dict(self):
#         """Serializes the object to a dictionary."""
#         return {"title": self.title, "text": self.text}

#     @classmethod
#     def from_dict(cls, data):
#         """Deserializes a dictionary to a SemanticSection object."""
#         return cls(data["title"], data["text"])

#     def __repr__(self):
#         return f"SemanticSection(title={self.title!r}, text={self.text!r})"


# class SemanticArticle:
#     sections: List[SemanticSection]
