# import instructor
# from openai import OpenAI
# from pydantic import BaseModel, Field

# # Enables `response_model`
# client = instructor.patch(
#     OpenAI(api_key="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")
# )


# class SemanticSection(BaseModel):
#     title: str = Field(description="The title of the section.")
#     text: str = Field(description="Cleaned text of the section.")

#     def to_dict(self):
#         return {"title": self.title, "text": self.text}


# class SemanticArticle(BaseModel):
#     sections: list[SemanticSection]


# def get_article(content) -> SemanticArticle:
#     return client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         response_model=SemanticArticle,
#         messages=[
#             {"role": "user", "content": "Extract {content}"},
#         ],
#     )
