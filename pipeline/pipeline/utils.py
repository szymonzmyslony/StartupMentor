import os
import json


def extract_manual_docs(directory_path):
    """
    Extracts dictionaries from JSON files in the specified directory where 'include' key is True.

    Parameters:
    directory_path (str): The path to the directory containing the JSON files.

    Returns:
    list: A list of dictionaries extracted from the JSON files, excluding the 'include' key.
    """
    included_dicts = []  # Array to hold the filtered dictionaries

    # Iterate over each file in the given directory
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)  # Full path to the file

        if os.path.isfile(file_path):  # Ensure it's a file
            with open(file_path, "r") as file:  # Open the file
                try:
                    data = json.load(file)  # Parse the JSON content

                    # Check if 'include' key exists and is True
                    if data.get("include", False):
                        del data["include"]  # Remove the 'include' key
                        included_dicts.append(data)  # Append the modified dictionary
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file {filename}")

    return included_dicts
