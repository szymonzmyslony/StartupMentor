import os
import json


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
